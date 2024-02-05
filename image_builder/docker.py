import os
import subprocess
import time

from image_builder.const import PUBLIC_REGISTRY


class DockerError(Exception):
    pass


class DockerStartTimeoutError(DockerError):
    pass


class DockerNotInstalledError(DockerError):
    pass


class Docker:
    @staticmethod
    def start(repository=None):
        if not Docker.running():
            subprocess.Popen(
                "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock "
                "--host=tcp://127.0.0.1:2375 --storage-driver=overlay2",
                shell=True,
            )

        counter = 0
        while not Docker.running():
            counter += 1
            if counter > 60:
                raise DockerStartTimeoutError()
            time.sleep(1)

        _, _, _, region, account, _, _ = os.environ["CODEBUILD_BUILD_ARN"].split(":")

        if repository and PUBLIC_REGISTRY in repository:
            repository_host = PUBLIC_REGISTRY
        else:
            repository_host = f"{account}.dkr.ecr.{region}.amazonaws.com"

        subprocess.run(
            f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {repository_host}",
            stdout=subprocess.PIPE,
            shell=True,
        )

    @staticmethod
    def running() -> bool:
        result = subprocess.run("docker ps", stdout=subprocess.PIPE, shell=True)
        if result.returncode == 127:
            raise DockerNotInstalledError()
        return result.returncode == 0
