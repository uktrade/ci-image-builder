import os
import subprocess
import unittest
from datetime import datetime
from test.doubles.process import StubbedProcess
from unittest.mock import call
from unittest.mock import patch

import boto3
import pytest
from botocore.stub import Stubber

from image_builder.docker import Docker
from image_builder.docker import DockerNotInstalledError
from image_builder.docker import DockerStartTimeoutError


class TestDocker(unittest.TestCase):
    returncode_docker_not_installed = 127
    returncode_docker_running = 0
    returncode_docker_wont_start = 1
    returncodes_docker_ps_successful_on_5th_attempt = [1, 1, 1, 1, 0]

    def setUp(self):
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"
        self.ssm_client = boto3.client("ssm")
        self.ssm_client_stub = Stubber(self.ssm_client)
        self.ssm_client_stub.add_response(
            "get_parameter",
            {
                "Parameter": {
                    "Name": "/codebuild/docker_hub_credentials",
                    "Type": "SecureString",
                    "Value": '{"username":"USER","password":"PASS"}',
                    "Version": 123,
                    "Selector": "string",
                    "SourceResult": "string",
                    "LastModifiedDate": datetime(2015, 1, 1),
                    "ARN": "string",
                    "DataType": "string",
                }
            },
            {
                "Name": "/codebuild/docker_hub_credentials",
                "WithDecryption": True,
            },
        )

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
        with self.ssm_client_stub:
            Docker.login(registry="public.ecr.aws", ssm_client=self.ssm_client)

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
        with self.ssm_client_stub:
            Docker.login(
                registry="000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                ssm_client=self.ssm_client,
            )

        run.assert_has_calls(
            [
                call(
                    f"aws ecr get-login-password --region oz-wizd-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
            ]
        )

    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_running),
    )
    def test_docker_login_to_docker_hub(self, run):
        os.environ["CODESTAR_CONNECTION_ARN"] = "something"

        with self.ssm_client_stub:
            Docker.login(
                registry="000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                ssm_client=self.ssm_client,
            )

        run.assert_has_calls(
            [
                call(
                    "docker login --username USER --password PASS",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
                call(
                    f"aws ecr get-login-password --region oz-wizd-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
            ]
        )

    @patch(
        "subprocess.run",
        return_value=StubbedProcess(returncode=returncode_docker_running),
    )
    def test_docker_login_failed_logging_into_docker_hub(self, run):
        os.environ["CODESTAR_CONNECTION_ARN"] = "something"

        self.ssm_client_stub.add_client_error("get_parameter")

        with self.ssm_client_stub:
            Docker.login(
                registry="000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                ssm_client=self.ssm_client,
            )

        run.assert_has_calls(
            [
                call(
                    f"aws ecr get-login-password --region oz-wizd-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.oz-wizd-1.amazonaws.com",
                    stdout=subprocess.PIPE,
                    shell=True,
                ),
            ]
        )
