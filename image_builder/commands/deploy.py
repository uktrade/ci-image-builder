import json
import os
import subprocess
from json import JSONDecodeError
from pathlib import Path

import click
import requests

from image_builder.const import ECR_REPO
from image_builder.docker import Docker
from image_builder.notify import Notify
from image_builder.progress import Progress


class DeployError(Exception):
    pass


class CannotDetectImageTagDeployError(DeployError):
    pass


class MissingConfigurationDeployError(DeployError):
    pass


class CannotCloneDeployRepositoryDeployError(DeployError):
    pass


class CannotInstallCopilotDeployError(DeployError):
    pass


@click.command("deploy", help="Deploy an image to a list of services.")
@click.option(
    "--send-notifications",
    is_flag=True,
    default=False,
    help="Send slack notifications.",
)
def deploy(send_notifications):
    try:
        clone_deployment_repository()
        copilot_version, version_cached = install_copilot()
        tag = get_image_tag_for_deployment()
        os.environ["IMAGE_TAG"] = tag

        repository = get_image_repository_url()
        Docker.login(repository.split("/")[0])
        timestamp = get_deployment_reference(repository, tag)
        notify = Notify(send_notifications)
        notify.reference = timestamp

        copilot_environment = os.getenv("COPILOT_ENVIRONMENT")
        copilot_services = os.getenv("COPILOT_SERVICES", "").split(" ")
        codebase_repository = os.getenv("CODEBASE_REPOSITORY")
        commit_hash = tag.replace("commit-", "")

        text_blocks = {
            "repository_name": codebase_repository,
            "revision_commit": commit_hash,
            "repository_url": f"https://github.com/{codebase_repository}",
        }

        progress = Progress()
        progress.set_current_phase("deploy")
        progress.current_phase_running()
        notify.post_build_progress(progress, text_blocks)
        notify.post_job_comment(
            f"{codebase_repository}@{commit_hash} deploying to {copilot_environment}",
            [
                f"<https://github.com/{codebase_repository}/commit/{commit_hash}|"
                f"{codebase_repository}@{commit_hash}> deploying to `{copilot_environment}` "
                f"| <{notify.get_build_url()}|Build Log>",
            ],
        )

        if not check_copilot_version(copilot_version):
            notify.post_job_comment(
                "Warning: A newer version of copilot-cli is available",
                [
                    "Warning: A newer version of `copilot-cli` is available. "
                    "Download the <https://github.com/aws/copilot-cli/releases/latest|latest version> "
                    "and update the `.copilot-version` file"
                ],
            )

        if not version_cached:
            notify.post_job_comment(
                "Warning: copilot version is not cached",
                [
                    f"Warning: copilot version `{copilot_version}` is not cached. "
                    "This version should be added to the `ci-image-builder` Dockerfile"
                ],
            )

        deploy_command = f"/copilot/./copilot-{copilot_version} deploy --env {copilot_environment} --deploy-env=false --force"
        for i, service in enumerate(copilot_services):
            deploy_command += f" --name {service}/{i + 1}"

        result = subprocess.run(
            deploy_command, stdout=subprocess.PIPE, shell=True, cwd=Path("./deploy")
        )

        if result.returncode != 0:
            progress.current_phase_failure()
            deploy_status_msg = "failed to deploy to"
        else:
            progress.current_phase_success()
            deploy_status_msg = "deployed to"

        notify.post_build_progress(progress, text_blocks)
        notify.post_job_comment(
            f"{codebase_repository}@{commit_hash} {deploy_status_msg} {copilot_environment}",
            [
                f"<https://github.com/{codebase_repository}/commit/{commit_hash}|"
                f"{codebase_repository}@{commit_hash}> {deploy_status_msg} `{copilot_environment}` "
                f"| <{notify.get_build_url()}|Build Log>",
            ],
            True,
        )

        if result.returncode != 0:
            raise DeployError("Failed to deploy")

    except DeployError as e:
        click.secho(f"{e.__class__.__name__}: {e}", fg="red")
        exit(1)


def get_image_repository_url() -> str:
    account_id = os.getenv("AWS_ACCOUNT_ID")
    region = os.getenv("AWS_REGION")
    ecr_repository = os.getenv(ECR_REPO)
    if not (account_id and region and ecr_repository):
        raise MissingConfigurationDeployError(
            "AWS_ACCOUNT_ID, AWS_REGION and ECR_REPOSITORY must be set"
        )

    repository_url = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repository}"
    click.echo(f"Found ECR Repository URL {repository_url}")
    return repository_url


def get_deployment_reference(repository: str, tag: str) -> str:
    regctl = subprocess.run(
        f"regctl image config {repository}:{tag}", stdout=subprocess.PIPE, shell=True
    )

    image_timestamp = None
    try:
        image_timestamp = json.loads(regctl.stdout)["config"]["Labels"][
            "uk.gov.trade.digital.build.timestamp"
        ]
    except (FileNotFoundError, JSONDecodeError, KeyError):
        pass

    if not image_timestamp:
        raise MissingConfigurationDeployError("Image contains no timestamp")

    click.echo(f"Found image timestamp {image_timestamp}")
    return image_timestamp


def get_image_tag_for_deployment() -> str:
    image_tag = os.getenv("IMAGE_TAG")
    if image_tag:
        return image_tag

    click.echo("No IMAGE_TAG set, assuming this run is in pipeline")

    image_detail = None
    try:
        image_detail = json.loads(
            Path(os.getenv("CODEBUILD_SRC_DIR", "."))
            .joinpath("imageDetail.json")
            .read_text()
        )
    except (FileNotFoundError, JSONDecodeError):
        pass

    if not image_detail:
        raise CannotDetectImageTagDeployError("No imageDetail.json found")

    matching_tag = None
    for tag in image_detail["ImageTags"]:
        if tag.startswith(os.getenv("ECR_TAG_PATTERN")):
            matching_tag = tag
            break

    if not matching_tag:
        raise CannotDetectImageTagDeployError(
            "imageDetail.json does not contain a matching tag"
        )

    commit_tag = None
    for tag in image_detail["ImageTags"]:
        if tag.startswith("commit-"):
            commit_tag = tag
            break

    if not commit_tag:
        raise CannotDetectImageTagDeployError(
            "imageDetail.json does not contain a commit tag"
        )

    click.echo(f"Found matching tag {commit_tag}")
    return commit_tag


def clone_deployment_repository():
    region = os.getenv("AWS_REGION")
    account = os.getenv("AWS_ACCOUNT_ID")
    codestar_connection_id = os.getenv("CODESTAR_CONNECTION_ID")
    deploy_repository = os.getenv("DEPLOY_REPOSITORY")
    branch_var = os.getenv("DEPLOY_REPOSITORY_BRANCH")
    branch_option = "" if not branch_var else f" --branch {branch_var}"

    if not (region and account and codestar_connection_id and deploy_repository):
        raise CannotCloneDeployRepositoryDeployError(
            "Cannot clone deploy repository if AWS_REGION, AWS_ACCOUNT_ID, CODESTAR_CONNECTION_ID "
            "and DEPLOY_REPOSITORY environment variables not set."
        )

    click.echo(f"Cloning repository {deploy_repository}")
    proc = subprocess.run(
        f"git clone https://codestar-connections.{region}.amazonaws.com/git-http/{account}/"
        f"{region}/{codestar_connection_id}/{deploy_repository}.git{branch_option} deploy",
        stdout=subprocess.PIPE,
        shell=True,
    )

    if proc.returncode != 0:
        raise CannotCloneDeployRepositoryDeployError(
            f"Failed to clone deploy repository: " f"{proc.stderr}"
        )


def install_copilot() -> (str, bool):
    cached = True

    try:
        version = open("deploy/.copilot-version").read().rstrip("\n")
    except FileNotFoundError:
        raise CannotInstallCopilotDeployError(
            "Cannot find .copilot-version file in deploy repository"
        )

    click.echo(f"Using copilot version {version}")
    proc = subprocess.run(
        f"/copilot/./copilot-{version} --version",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    if proc.returncode != 0:
        click.echo(f"Copilot version {version} not pre-installed, installing now")
        cached = False

        proc = subprocess.run(
            f"wget -q -O copilot-{version} https://ecs-cli-v2-release.s3.amazonaws.com/copilot-linux-v{version} && "
            f"chmod +x ./copilot-{version} && mv copilot-{version} /copilot",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )

        if proc.returncode != 0:
            raise CannotInstallCopilotDeployError(
                f"Failed to install copilot version {version}: " f"{proc.stderr}"
            )

    return version, cached


def check_copilot_version(version):
    response = requests.get("https://github.com/aws/copilot-cli/releases/latest")
    release_version = response.url.split("/").pop().replace("v", "")
    return release_version == version
