import json
import os
import subprocess
from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.process import StubbedProcess
from unittest.mock import call
from unittest.mock import patch

from click.testing import CliRunner
from parameterized import parameterized

from image_builder.commands.deploy import clone_deployment_repository
from image_builder.commands.deploy import deploy
from image_builder.const import ECR_REPO

DEFAULT_TEST_COPILOT_VERSION = "1.33.1"
FAILING_TEST_COPILOT_VERSION = "1.31.0"

COMMAND_PATTERNS = {
    "regctl": StubbedProcess(
        stdout=json.dumps(
            {
                "config": {
                    "Labels": {
                        "uk.gov.trade.digital.build.timestamp": "00000000",
                    },
                },
            }
        )
    ),
    "git clone": StubbedProcess(returncode=0),
    "wget": StubbedProcess(returncode=0),
    "chmod": StubbedProcess(returncode=0),
    f"/copilot/./copilot-{DEFAULT_TEST_COPILOT_VERSION} deploy": StubbedProcess(
        returncode=0
    ),
    f"/copilot/./copilot-{DEFAULT_TEST_COPILOT_VERSION} --version": StubbedProcess(
        returncode=0
    ),
    f"/copilot/./copilot-{FAILING_TEST_COPILOT_VERSION} --version": StubbedProcess(
        returncode=1
    ),
    "/copilot/./copilot-test --version": StubbedProcess(returncode=1),
}


def call_subprocess_run(
    command: str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd="."
):
    for pattern in COMMAND_PATTERNS.keys():
        if command.startswith(pattern):
            return COMMAND_PATTERNS[pattern]

    return StubbedProcess(returncode=0)


@patch("subprocess.Popen")
@patch("subprocess.run", wraps=call_subprocess_run)
@patch("image_builder.commands.deploy.Notify")
@patch("image_builder.commands.deploy.Docker")
class TestDeployCommand(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()
        self.fs.create_dir("/src")
        self.fs.create_file(
            "deploy/.copilot-version", contents=DEFAULT_TEST_COPILOT_VERSION
        )

    @staticmethod
    def setup_mocks(docker, notify, subprocess_run, subprocess_popen):
        docker.running.return_value = True
        subprocess_popen.return_value = StubbedProcess()
        notify().get_build_url.return_value = "https://example.com/build_url"

    @staticmethod
    def run_deploy():
        runner = CliRunner()
        result = runner.invoke(deploy, ["--send-notifications"])
        return result

    @staticmethod
    def setup_environment():
        os.environ["AWS_ACCOUNT_ID"] = "00000000000"
        os.environ["AWS_REGION"] = "eu-west-2"
        os.environ["CODEBASE_REPOSITORY"] = "organisation/repository"
        os.environ["CODEBUILD_SRC_DIR"] = "/src"
        os.environ["CODESTAR_CONNECTION_ID"] = "00000000-0000-0000-0000-000000000000"
        os.environ["COPILOT_ENVIRONMENT"] = "dev"
        os.environ["COPILOT_SERVICES"] = "web worker"
        os.environ["DEPLOY_REPOSITORY"] = "organisation/repository-deploy"
        os.environ[ECR_REPO] = "repository/application"
        os.environ["ECR_TAG_PATTERN"] = "branch-main"
        os.environ["IMAGE_TAG"] = "commit-99999"

    @staticmethod
    def teardown_environment():
        if os.getenv("AWS_ACCOUNT_ID"):
            del os.environ["AWS_ACCOUNT_ID"]
        if os.getenv("AWS_REGION"):
            del os.environ["AWS_REGION"]
        if os.getenv("CODEBASE_REPOSITORY"):
            del os.environ["CODEBASE_REPOSITORY"]
        if os.getenv("CODEBUILD_SRC_DIR"):
            del os.environ["CODEBUILD_SRC_DIR"]
        if os.getenv("CODESTAR_CONNECTION_ID"):
            del os.environ["CODESTAR_CONNECTION_ID"]
        if os.getenv("COPILOT_ENVIRONMENT"):
            del os.environ["COPILOT_ENVIRONMENT"]
        if os.getenv("COPILOT_SERVICES"):
            del os.environ["COPILOT_SERVICES"]
        if os.getenv("DEPLOY_REPOSITORY"):
            del os.environ["DEPLOY_REPOSITORY"]
        if os.getenv(ECR_REPO):
            del os.environ[ECR_REPO]
        if os.getenv("ECR_TAG_PATTERN"):
            del os.environ["ECR_TAG_PATTERN"]
        if os.getenv("IMAGE_TAG"):
            del os.environ["IMAGE_TAG"]

    @patch("image_builder.commands.deploy.check_copilot_version", return_value=True)
    def test_perfect_deploy(
        self, check_copilot_version, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ["IMAGE_TAG"]

        self.fs.create_file(
            "/src/imageDetail.json",
            contents=json.dumps(
                {
                    "ImageTags": [
                        "branch-main",
                        "commit-99999",
                        "latest",
                    ],
                }
            ),
        )

        result = self.run_deploy()

        self.assertIn(
            "Cloning repository organisation/repository-deploy", result.output
        )
        self.assertIn("Found matching tag commit-99999", result.output)
        self.assertIn(
            "Found ECR Repository URL 00000000000.dkr.ecr.eu-west-2.amazonaws.com/repository/application",
            result.output,
        )
        self.assertIn("Found image timestamp 00000000", result.output)

        subprocess_run.assert_has_calls(
            [
                call(
                    "git clone https://codestar-connections.eu-west-2.amazonaws.com/git-http/00000000000"
                    "/eu-west-2/00000000-0000-0000-0000-000000000000/organisation/repository-deploy.git "
                    "deploy",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
                call(
                    f"/copilot/./copilot-{DEFAULT_TEST_COPILOT_VERSION} --version",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                ),
                call(
                    "regctl image config 00000000000.dkr.ecr.eu-west-2.amazonaws.com/repository/application:commit-99999",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
                call(
                    f"/copilot/./copilot-{DEFAULT_TEST_COPILOT_VERSION} deploy"
                    f" --env dev --deploy-env=false --force --name web/1 --name worker/2",
                    stdout=subprocess.PIPE,
                    shell=True,
                    cwd=Path("deploy"),
                ),
            ],
            any_order=False,
        )

        notify().post_job_comment.assert_has_calls(
            [
                call(
                    "organisation/repository@99999 deploying to dev",
                    [
                        "<https://github.com/organisation/repository/commit/99999|organisation/"
                        "repository@99999> deploying to `dev` | <https://example.com/build_url"
                        "|Build Log>",
                    ],
                ),
                call(
                    "organisation/repository@99999 deployed to dev",
                    [
                        "<https://github.com/organisation/repository/commit/99999|organisation/"
                        "repository@99999> deployed to `dev` | <https://example.com/build_url"
                        "|Build Log>",
                    ],
                    True,
                ),
            ],
            any_order=False,
        )
        self.teardown_environment()

    def test_when_cloning_deploy_repo_fails_when_git_clone_errors(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        COMMAND_PATTERNS["git clone"] = StubbedProcess(returncode=1)

        result = self.run_deploy()

        self.assertIn(
            "Cloning repository organisation/repository-deploy", result.output
        )
        self.assertIn(
            "CannotCloneDeployRepositoryDeployError: Failed to clone deploy repository",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    @parameterized.expand(
        [
            "AWS_REGION",
            "AWS_ACCOUNT_ID",
            "CODESTAR_CONNECTION_ID",
            "DEPLOY_REPOSITORY",
        ]
    )
    def test_when_cloning_deploy_repo_fails_when_configuration_not_set(
        self, docker, notify, subprocess_run, subprocess_popen, env_to_remove
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ[env_to_remove]

        result = self.run_deploy()

        self.assertIn(
            "CannotCloneDeployRepositoryDeployError: Cannot clone deploy repository if AWS_REGION, AWS_ACCOUNT_ID, "
            "CODESTAR_CONNECTION_ID and DEPLOY_REPOSITORY environment variables not "
            "set.",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_get_image_tag_for_deployment_fails_when_no_codebuild_src_dir(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ["IMAGE_TAG"]
        del os.environ["CODEBUILD_SRC_DIR"]

        result = self.run_deploy()

        self.assertIn(
            "No IMAGE_TAG set, assuming this run is in pipeline", result.output
        )
        self.assertIn(
            "CannotDetectImageTagDeployError: No imageDetail.json found", result.output
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_get_image_tag_for_deployment_fails_when_no_expected_image_detail(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ["IMAGE_TAG"]

        result = self.run_deploy()

        self.assertIn(
            "No IMAGE_TAG set, assuming this run is in pipeline", result.output
        )
        self.assertIn(
            "CannotDetectImageTagDeployError: No imageDetail.json found", result.output
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_get_image_tag_for_deployment_fails_when_no_matching_tag_found_in_image_detail(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ["IMAGE_TAG"]
        self.fs.create_file(
            "/src/imageDetail.json",
            contents=json.dumps(
                {
                    "ImageTags": [
                        "commit-99999",
                        "latest",
                    ],
                }
            ),
        )

        result = self.run_deploy()

        self.assertIn(
            "No IMAGE_TAG set, assuming this run is in pipeline", result.output
        )
        self.assertIn(
            "CannotDetectImageTagDeployError: imageDetail.json does not contain a matching tag",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_get_image_repository_url_fails_when_ecr_repository_not_set(
        self,
        docker,
        notify,
        subprocess_run,
        subprocess_popen,
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        del os.environ[ECR_REPO]

        result = self.run_deploy()

        self.assertIn(
            "MissingConfigurationDeployError: AWS_ACCOUNT_ID, AWS_REGION and "
            "ECR_REPOSITORY must be set",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_get_deployment_reference_fails_timestamp_label_not_set(
        self,
        docker,
        notify,
        subprocess_run,
        subprocess_popen,
    ):
        old_regctl = COMMAND_PATTERNS["regctl"]
        try:
            self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
            self.setup_environment()

            COMMAND_PATTERNS["regctl"] = StubbedProcess(
                stdout=json.dumps(
                    {
                        "config": {},
                    }
                )
            )

            result = self.run_deploy()

            self.assertIn(
                "MissingConfigurationDeployError: Image contains no timestamp",
                result.output,
            )

            self.assertEqual(result.exit_code, 1)
            self.teardown_environment()
        finally:
            COMMAND_PATTERNS["regctl"] = old_regctl

    @patch("image_builder.commands.deploy.check_copilot_version", return_value=True)
    def test_installing_copilot(
        self, check_copilot_version, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()

        result = self.run_deploy()

        self.assertIn(
            f"Using copilot version {DEFAULT_TEST_COPILOT_VERSION}",
            result.output,
        )
        self.assertNotIn(
            "Failed to install copilot version test",
            result.output,
        )

        self.assertEqual(result.exit_code, 0)
        self.teardown_environment()

    def test_installing_copilot_fails_when_no_version_file_present(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        self.fs.remove_object("deploy/.copilot-version")

        result = self.run_deploy()

        self.assertIn(
            "CannotInstallCopilotDeployError: Cannot find .copilot-version file in deploy repository",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()

    def test_installing_copilot_fails_when_version_fails_to_install(
        self, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        self.fs.remove_object("deploy/.copilot-version")
        self.fs.create_file("deploy/.copilot-version", contents="test")
        COMMAND_PATTERNS["/copilot/./copilot-test --version"] = StubbedProcess(
            returncode=1
        )
        COMMAND_PATTERNS["wget"] = StubbedProcess(returncode=1)

        result = self.run_deploy()

        self.assertIn(
            "Failed to install copilot version test",
            result.output,
        )

        self.assertEqual(result.exit_code, 1)
        self.teardown_environment()
        COMMAND_PATTERNS["wget"] = StubbedProcess(returncode=0)

    @patch("image_builder.commands.deploy.check_copilot_version", return_value=True)
    def test_installing_copilot_succeeds_when_preinstalled_version_does_not_exist(
        self, check_copilot_version, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()
        self.fs.remove_object("deploy/.copilot-version")
        self.fs.create_file(
            "deploy/.copilot-version", contents=FAILING_TEST_COPILOT_VERSION
        )
        COMMAND_PATTERNS[
            f"/copilot/./copilot-{FAILING_TEST_COPILOT_VERSION} --version"
        ] = StubbedProcess(returncode=1)

        result = self.run_deploy()

        self.assertIn(
            f"Copilot version {FAILING_TEST_COPILOT_VERSION} not pre-installed, installing now",
            result.output,
        )

        notify().post_job_comment.assert_has_calls(
            [
                call(
                    "Warning: copilot version is not cached",
                    [
                        f"Warning: copilot version `{FAILING_TEST_COPILOT_VERSION}` is not cached. "
                        "This version should be added to the `ci-image-builder` Dockerfile"
                    ],
                )
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.teardown_environment()

    @patch("image_builder.commands.deploy.check_copilot_version", return_value=False)
    def test_sending_notification_when_copilot_version_behind_latest(
        self, check_copilot_version, docker, notify, subprocess_run, subprocess_popen
    ):
        self.setup_mocks(docker, notify, subprocess_run, subprocess_popen)
        self.setup_environment()

        result = self.run_deploy()

        notify().post_job_comment.assert_has_calls(
            [
                call(
                    "Warning: A newer version of copilot-cli is available",
                    [
                        "Warning: A newer version of `copilot-cli` is available. "
                        "Download the <https://github.com/aws/copilot-cli/releases/latest|latest version> "
                        "and update the `.copilot-version` file"
                    ],
                ),
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.teardown_environment()


@patch("subprocess.run")
def test_clone_deployment_repository(mock_run):
    TestDeployCommand.setup_environment()
    mock_run.return_value = StubbedProcess()

    clone_deployment_repository()

    mock_run.assert_called_with(
        "git clone https://codestar-connections.eu-west-2.amazonaws.com/git-http/00000000000/eu-west-2/"
        "00000000-0000-0000-0000-000000000000/organisation/repository-deploy.git deploy",
        stdout=subprocess.PIPE,
        shell=True,
    )

    TestDeployCommand.teardown_environment()


@patch("subprocess.run")
def test_clone_deployment_repository_with_deploy_repo_branch_set(mock_run):
    TestDeployCommand.setup_environment()
    mock_run.return_value = StubbedProcess()
    os.environ["DEPLOY_REPOSITORY_BRANCH"] = "feature-branch"

    clone_deployment_repository()

    mock_run.assert_called_with(
        "git clone https://codestar-connections.eu-west-2.amazonaws.com/git-http/00000000000/eu-west-2/"
        "00000000-0000-0000-0000-000000000000/organisation/repository-deploy.git --branch feature-branch deploy",
        stdout=subprocess.PIPE,
        shell=True,
    )

    TestDeployCommand.teardown_environment()
