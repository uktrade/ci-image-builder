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
    def start():
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

    @staticmethod
    def login(registry):
        if registry == PUBLIC_REGISTRY:
            command = f"aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin {registry}"
        else:
            command = f"aws ecr get-login-password --region {registry.split('.')[3]} | docker login --username AWS --password-stdin {registry}"

        print(f"Running command: {command}")
        subprocess.run(
            f"{command}",
            stdout=subprocess.PIPE,
            shell=True,
        )

    @staticmethod
    def running() -> bool:
        result = subprocess.run("docker ps", stdout=subprocess.PIPE, shell=True)
        if result.returncode == 127:
            raise DockerNotInstalledError()
        return result.returncode == 0
