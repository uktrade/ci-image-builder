import subprocess
from typing import Callable

from image_builder.codebase.codebase import Codebase
from image_builder.publish import publish_to_additional_repository


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
            self.get_command(publish),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        while proc.poll() is None:
            output = proc.stdout.readline()
            print(output, end="")
            if on_building is not None and "===> BUILDING" in output:
                on_building()
            if on_exporting is not None and "===> EXPORTING" in output:
                on_exporting()

        if proc.returncode != 0:
            error = proc.stderr.read()

            # To account for different systems (macOS produces a byte array, linux produces a str)
            if hasattr(error, "decode"):
                error = error.decode("utf-8")

            raise PackCommandFailedError(
                error[len(error) - 2500 :] if len(error) > 2500 else error
            )

        if publish and self.codebase.build.additional_repository:
            publish_to_additional_repository(
                self.codebase.build.repository,
                self.codebase.build.additional_repository,
                self.codebase.revision.get_docker_tags(),
            )

    def get_command(self, publish=False):
        buildpacks = " ".join([f"--buildpack {p}" for p in self.get_buildpacks()])
        environment = " ".join([f"--env {e}" for e in self.get_environment()])
        tags = " ".join(
            [
                f"--tag {self._repository}:{t}"
                for t in self.codebase.revision.get_docker_tags()
            ]
        )
        command = (
            f"pack build {self._repository} "
            f"--builder {self.codebase.build.builder.name}:{self.codebase.build.builder.version} "
            f"{tags} {environment} {buildpacks}"
        )

        if publish:
            command += f" --publish --cache-image {self._repository}:cache"
        return command

    def get_buildpacks(self):
        buildpacks = ["paketo-buildpacks/git"]

        if self.codebase.build.packages:
            buildpacks.append("fagiani/apt")

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

        environment.append(f"BP_OCI_REF_NAME={self.get_bp_oci_ref_name()}")
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

    def get_bp_oci_ref_name(self):
        if self.codebase.revision.tag:
            return f"tag-{self.codebase.revision.tag}"

        return f"commit-{self.codebase.revision.commit}"

    @property
    def _repository(self):
        return self.codebase.build.repository
