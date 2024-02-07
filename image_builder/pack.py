import subprocess
from typing import Callable

from image_builder.codebase.codebase import Codebase


class PackError(Exception):
    pass


class PackCommandFailedError(PackError):
    pass


class Pack:
    codebase: Codebase
    build_timestamp: str

    def __init__(self, codebase: Codebase, build_timestamp: str = None):
        self.codebase = codebase
        self.build_timestamp = build_timestamp

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
        tags = " ".join([f"--tag {self.repository}:{t}" for t in self.get_tags()])
        command = (
            f"pack build {self.repository} "
            f"--builder {self.codebase.build.builder.name}:{self.codebase.build.builder.version} "
            f"{tags} {environment} {buildpacks} "
        )

        if publish:
            command += f"--publish --cache-image {self.repository}:cache"
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
        buildpacks.append("gcr.io/paketo-buildpacks/image-labels")
        buildpacks.append("gcr.io/paketo-buildpacks/environment-variables")

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
            environment.append(f"BPE_GIT_TAG={self.codebase.revision.tag}")

        if self.codebase.revision.commit:
            environment.append(f"BPE_GIT_COMMIT={self.codebase.revision.commit}")
            environment.append(f"BP_OCI_REVISION={self.codebase.revision.commit}")
            environment.append(f"BP_OCI_VERSION={self.codebase.revision.commit}")

        if self.codebase.revision.branch:
            environment.append(f"BPE_GIT_BRANCH={self.codebase.revision.branch}")

        environment.append(f"BP_OCI_REF_NAME={self.codebase.build.repository}")
        environment.append(
            f"BP_OCI_SOURCE={self.codebase.revision.get_repository_url()}"
        )

        additional_labels = []

        if self.build_timestamp is not None:
            additional_labels.append(
                f"uk.gov.trade.digital.build.timestamp={self.build_timestamp}"
            )

        if additional_labels:
            additional_labels = " ".join(additional_labels)
            environment.append(f'BP_IMAGE_LABELS="{additional_labels}"')

        return environment

    def get_tags(self):
        tags = [f"commit-{self.codebase.revision.commit}"]
        if self.codebase.revision.tag:
            tags.append(f"tag-{self.codebase.revision.tag}")
            tags.append(f"tag-latest")

        if self.codebase.revision.branch:
            tags.append(f"branch-{self.codebase.revision.branch.replace('/', '-')}")

        return tags

    @property
    def repository(self):
        return self.codebase.build.repository
