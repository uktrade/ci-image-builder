import os
import subprocess
import unittest
from test.doubles.process import StubbedProcess
from unittest.mock import call, patch

import pytest

from image_builder.docker import (Docker, DockerNotInstalledError,
                                  DockerStartTimeoutError)


class TestDocker(unittest.TestCase):
    returncode_docker_not_installed = 127
    returncode_docker_running = 0
    returncode_docker_wont_start = 1
    returncodes_docker_ps_successful_on_5th_attempt = [1, 1, 1, 1, 0]

    def setUp(self):
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

    @patch("subprocess.Popen", return_value=None)
    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_running),
    )
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_already_running(self, sleep, run, popen):
        Docker.start()

        run.assert_has_calls(
            [
                call("docker ps", stdout=subprocess.PIPE, shell=True),
            ]
        )
        popen.assert_not_called()
        sleep.assert_not_called()

    @patch("subprocess.Popen", return_value=None)
    @patch(
        "subprocess.run",
        return_value=StubbedProcess(
            returncodes=returncodes_docker_ps_successful_on_5th_attempt
        ),
    )
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_not_running(self, sleep, run, popen):
        Docker.start()

        run.assert_has_calls(
            [
                call("docker ps", stdout=subprocess.PIPE, shell=True),
            ]
        )
        popen.assert_called_with(
            "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock "
            "--host=tcp://127.0.0.1:2375 --storage-driver=overlay2",
            shell=True,
        )
        sleep.assert_called_with(1)

    @patch("subprocess.Popen", return_value=None)
    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_not_installed),
    )
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_not_installed(self, sleep, run, popen):
        with pytest.raises(DockerNotInstalledError):
            Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_not_called()
        sleep.assert_not_called()

    @patch("subprocess.Popen", return_value=None)
    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_wont_start),
    )
    @patch("time.sleep", return_value=None)
    def test_docker_never_starts(self, sleep, run, popen):
        with pytest.raises(DockerStartTimeoutError):
            Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_called_with(
            "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock "
            "--host=tcp://127.0.0.1:2375 --storage-driver=overlay2",
            shell=True,
        )
        sleep.assert_has_calls([call(1)] * 60)

    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_running),
    )
    def test_docker_login_with_public_repository(self, run):
        Docker.login(registry="public.ecr.aws")

        run.assert_has_calls(
            [
                call(
                    f"aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
            ]
        )

    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_running),
    )
    def test_docker_login_with_private_repository(self, run):
        Docker.login(registry="000000000000.dkr.ecr.oz-wizd-1.amazonaws.com")

        run.assert_has_calls(
            [
                call(
                    f"aws ecr get-login-password --region oz-wizd-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
            ]
        )
