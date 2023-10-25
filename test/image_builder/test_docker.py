import subprocess
import unittest
from test.doubles.process import StubbedProcess
from unittest.mock import call
from unittest.mock import patch

import pytest

from image_builder.docker import Docker
from image_builder.docker import DockerNotInstalledError
from image_builder.docker import DockerStartTimeoutError


class TestDocker(unittest.TestCase):
    @patch("subprocess.Popen", return_value=None)
    @patch("subprocess.run", return_value=StubbedProcess())
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_already_running(self, sleep, run, popen):
        Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_not_called()
        sleep.assert_not_called()

    @patch("subprocess.Popen", return_value=None)
    @patch("subprocess.run", return_value=StubbedProcess(returncodes=[1, 1, 1, 1, 0]))
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_not_running(self, sleep, run, popen):
        Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_called_with(
            "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock "
            "--host=tcp://127.0.0.1:2375 --storage-driver=overlay2&",
            shell=True,
        )
        sleep.assert_called_with(1)

    @patch("subprocess.Popen", return_value=None)
    @patch("subprocess.run", return_value=StubbedProcess(returncode=127))
    @patch("time.sleep", return_value=None)
    def test_starting_docker_when_not_installed(self, sleep, run, popen):
        with pytest.raises(DockerNotInstalledError):
            Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_not_called()
        sleep.assert_not_called()

    @patch("subprocess.Popen", return_value=None)
    @patch("subprocess.run", return_value=StubbedProcess(returncode=1))
    @patch("time.sleep", return_value=None)
    def test_docker_never_starts(self, sleep, run, popen):
        with pytest.raises(DockerStartTimeoutError):
            Docker.start()

        run.assert_called_with("docker ps", stdout=subprocess.PIPE, shell=True)
        popen.assert_called_with(
            "nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock "
            "--host=tcp://127.0.0.1:2375 --storage-driver=overlay2&",
            shell=True,
        )
        sleep.assert_has_calls([call(1)] * 20)
