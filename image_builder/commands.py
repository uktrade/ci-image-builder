import click

from image_builder.codebase.codebase import Codebase
from image_builder.docker import Docker
from image_builder.notify import Notify
from image_builder.pack import Pack
from image_builder.progress import Progress


@click.command("build", help="Build an image")
@click.option("--publish", is_flag=True, default=False, help="Publish the built image")
def build(publish):
    if not Docker.running():
        click.echo("Docker is not running, starting up...")
        Docker.start()

    click.echo("Docker is running, continuing with build...")

    codebase = Codebase(".")
    notify = Notify(codebase)
    progress = Progress()
    pack = Pack(codebase)

    click.echo(
        "Found revision: "
        f"repository={codebase.revision.get_repository_name()}, "
        f"commit={codebase.revision.commit}, "
        f"branch={codebase.revision.branch}, "
        f"tag={codebase.revision.tag}"
    )

    click.echo(f"Found processes: {[p.name for p in codebase.processes]}")
    click.echo(f"Found languages: {codebase.languages}")
    click.echo(
        f"Using builder: {codebase.build.builder.name}@{codebase.build.builder.version}"
    )
    click.echo(f"Using buildpacks: {pack.get_buildpacks()}")

    progress.current_phase_running()
    notify.post_progress(progress)
    buildpacks = ", ".join(pack.get_buildpacks())
    processes = ", ".join(p.name for p in pack.codebase.processes)
    notify.post_job_comment(
        [
            f"*Repository*: {pack.codebase.revision.get_repository_name()}",
            f"*Commit*: {pack.codebase.revision.commit} "
            f"*Branch*: {pack.codebase.revision.branch} "
            f"*Tag*: {pack.codebase.revision.tag}",
            f"*Processes*: {processes}",
            f"*Languages*: {pack.codebase.languages}",
            f"*Builder*: {pack.codebase.build.builder.name}@{pack.codebase.build.builder.version}",
            f"*Buildpacks*: {buildpacks}",
        ]
    )

    try:
        pack.codebase.setup()
    except (Exception, KeyboardInterrupt) as e:
        progress.current_phase_failure()
        notify.post_progress(progress)
        notify.post_job_comment(
            [f"Build was cancelled: {e.__class__.__name__}", str(e)]
        )
        exit(1)

    try:
        try:
            pack.build(
                publish, on_building(notify, progress), on_publishing(notify, progress)
            )
            progress.current_phase_success()
            notify.post_progress(progress)
        except (Exception, KeyboardInterrupt) as e:
            progress.current_phase_failure()
            notify.post_progress(progress)
            notify.post_job_comment(
                [f"Build was cancelled: {e.__class__.__name__}", str(e)]
            )
            exit(1)

    finally:
        codebase.teardown()


def on_building(notify, progress):
    def on_building_callback():
        progress.current_phase_success()
        progress.set_current_phase("build")
        progress.current_phase_running()
        notify.post_progress(progress)

    return on_building_callback


def on_publishing(notify, progress):
    def on_publishing_callback():
        progress.current_phase_success()
        progress.set_current_phase("publish")
        progress.current_phase_running()
        notify.post_progress(progress)

    return on_publishing_callback
