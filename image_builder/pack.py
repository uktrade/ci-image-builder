import subprocess
from typing import Callable

from image_builder.codebase.codebase import Codebase


class PackError(Exception):
    pass


class PackCommandFailedError(PackError):
    pass


class Pack:
    codebase: Codebase

    def __init__(self, codebase: Codebase):
        self.codebase = codebase

    def build(
        self, publish=False, on_building: Callable = None, on_exporting: Callable = None
    ):
        proc = subprocess.Popen(
            self.get_command(publish), shell=True, stdout=subprocess.PIPE
        )

        while proc.poll() is None:
            output = proc.stdout.readline().decode()
            print(output, end="")
            if on_building is not None and "===> BUILDING" in output:
                on_building()
            if on_exporting is not None and "===> EXPORTING" in output:
                on_exporting()
        if proc.returncode != 0:
            raise PackCommandFailedError

    def get_command(self, publish=False):
        buildpacks = " ".join([f"--buildpack {p}" for p in self.get_buildpacks()])
        environment = " ".join([f"--env {e}" for e in self.get_environment()])
        tags = " ".join(
            [
                f"--tag {self.codebase.build.repository}:{t}"
                for t in self.get_additional_tags()
            ]
        )

        command = (
            f"pack build {self.codebase.build.repository}:{self.get_main_tag()} "
            f"--builder {self.codebase.build.builder.name}:{self.codebase.build.builder.version} "
            f"{tags} {environment} {buildpacks} "
        )

        if publish:
            command += f"--publish --cache-image {self.codebase.build.repository}-cache"
        return command

    def get_buildpacks(self):
        buildpacks = ["fagiani/apt", "paketo-buildpacks/git"]

        for pack in self.codebase.build.packs:
            buildpacks.append(pack.name)

        if "paketo-buildpacks/python" not in buildpacks:
            if "python" in self.codebase.languages:
                buildpacks.append("paketo-buildpacks/python")

        if "paketo-buildpacks/nodejs" not in buildpacks:
            if "nodejs" in self.codebase.languages:
                buildpacks.append("paketo-buildpacks/nodejs")

        buildpacks.append("fagiani/run")

        return buildpacks

    def get_environment(self):
        buildpacks = self.get_buildpacks()
        environment = []
        if "paketo-buildpacks/python" in buildpacks:
            python_version = self.codebase.languages["python"].version
            environment.append(f"BP_CPYTHON_VERSION={python_version}")

        if "paketo-buildpacks/nodejs" in buildpacks:
            node_version = self.codebase.languages["nodejs"].version
            environment.append(f"BP_NODE_VERSION={node_version}")

        if self.codebase.revision.tag:
            environment.append(f"GIT_TAG={self.codebase.revision.tag}")

        if self.codebase.revision.commit:
            environment.append(f"GIT_COMMIT={self.codebase.revision.commit}")

        if self.codebase.revision.branch:
            environment.append(f"GIT_BRANCH={self.codebase.revision.branch}")

        return environment

    def get_main_tag(self):
        return f"commit-{self.codebase.revision.commit}"

    def get_additional_tags(self):
        tags = []
        if self.codebase.revision.tag:
            tags.append(f"tag-{self.codebase.revision.tag}")

        if self.codebase.revision.branch:
            tags.append(f"branch-{self.codebase.revision.branch}")

        return tags