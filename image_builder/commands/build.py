import click

from image_builder.codebase.codebase import Codebase
from image_builder.docker import Docker
from image_builder.notify import Notify
from image_builder.pack import Pack
from image_builder.progress import Progress


@click.command("build", help="Build an image.")
@click.option("--publish", is_flag=True, default=False, help="Publish the built image.")
@click.option(
    "--send-notifications",
    is_flag=True,
    default=False,
    help="Send slack notifications.",
)
@click.option(
    "--with-runner-image",
    help="Specify a runner image to be used as the base for your application image.",
)
def build(publish, send_notifications, with_runner_image):
    codebase = Codebase(".")
    notify = Notify(send_notifications)
    progress = Progress()
    progress.current_phase_running()
    notify.post_build_progress(progress, codebase.get_notify_attrs())
    pack = Pack(codebase, notify.reference)
    try:
        if not Docker.running():
            click.echo("Docker is not running, starting up...")
            Docker.start()
        click.echo("Docker is running, continuing with build...")

        Docker.login(codebase.build.registry)

        click.echo(
            "Found revision: "
            f"repository={codebase.revision.get_repository_name()}, "
            f"commit={codebase.revision.commit}, "
            f"branch={codebase.revision.branch}, "
            f"tag={codebase.revision.tag}"
        )
        click.echo(f"Using ECR repository: {codebase.build.repository}")
        if publish and codebase.build.additional_repository:
            click.echo(
                f"Pushing image to additional ECR repository: {codebase.build.additional_repository}"
            )
        click.echo(f"Found processes: {[p.name for p in codebase.processes]}")
        click.echo(f"Found languages: {codebase.languages}")
        click.echo(
            f"Using builder: {codebase.build.builder.name}@{codebase.build.builder.version}"
        )
        click.echo(f"Using buildpacks: {pack.get_buildpacks()}")

        buildpacks = ", ".join(pack.get_buildpacks())
        processes = ", ".join(p.name for p in pack.codebase.processes)
        notify.post_job_comment(
            f"Build: {pack.codebase.revision.get_repository_name()}@{pack.codebase.revision.commit} update",
            [
                f"*GitHub Repository*: {pack.codebase.revision.get_repository_name()}",
                f"*Commit*: {pack.codebase.revision.commit} "
                f"*Branch*: {pack.codebase.revision.branch} "
                f"*Tag*: {pack.codebase.revision.tag}",
                f"*ECR Image*: {codebase.build.repository}:commit-{pack.codebase.revision.commit}",
                f"*Processes*: {processes}",
                f"*Languages*: {pack.codebase.languages}",
                f"*Builder*: {pack.codebase.build.builder.name}@{pack.codebase.build.builder.version}",
                f"*Buildpacks*: {buildpacks}",
            ],
        )

        pack.codebase.setup()

        pack.build(
            publish,
            on_building(notify, progress, codebase),
            on_publishing(notify, progress, codebase),
            with_runner_image,
        )

        progress.current_phase_success()
        notify.post_build_progress(progress, codebase.get_notify_attrs())

    except (Exception, KeyboardInterrupt) as e:
        reason = "Build was cancelled" if type(e) == KeyboardInterrupt else "Error"
        click.secho(f"{reason}: {str(e)}", fg="red")
        progress.current_phase_failure()
        notify.post_build_progress(progress, codebase.get_notify_attrs())
        notify.post_job_comment(
            f"Build: {pack.codebase.revision.get_repository_name()}@{pack.codebase.revision.commit} cancelled",
            [f"{reason}: {e.__class__.__name__}", str(e)],
        )
        exit(1)

    finally:
        codebase.teardown()


def on_building(notify, progress, codebase):
    def on_building_callback():
        progress.current_phase_success()
        progress.set_current_phase("build")
        progress.current_phase_running()
        notify.post_build_progress(progress, codebase.get_notify_attrs())

    return on_building_callback


def on_publishing(notify, progress, codebase):
    def on_publishing_callback():
        progress.current_phase_success()
        progress.set_current_phase("publish")
        progress.current_phase_running()
        notify.post_build_progress(progress, codebase.get_notify_attrs())

    return on_publishing_callback
