from test.base_test_case import BaseTestCase
from test.doubles.process import StubbedProcess
from unittest.mock import call
from unittest.mock import patch

import pytest

from image_builder.publish import publish_to_additional_repository
from image_builder.publish import run_and_check_result


@patch("image_builder.publish.Docker.login")
@patch("subprocess.run")
class TestPackPublishToAdditionalRepo(BaseTestCase):
    def test_publish_to_additional_calls_the_correct_commands(
        self, subprocess_popen, docker_login
    ):
        subprocess_popen.return_value = StubbedProcess(returncode=0)
        repository = "000000000000.dkr.ecr.region.amazonaws.com/my/repo"
        additional_repo = "public.ecr.aws/my/repo"
        tags = ["tag1", "tag2"]

        publish_to_additional_repository(repository, additional_repo, tags)

        docker_login.assert_called_with("public.ecr.aws")

        tagged_image_0 = f"{repository}:{tags[0]}"
        tagged_image_1 = f"{repository}:{tags[1]}"
        add_tagged_image_0 = f"{additional_repo}:{tags[0]}"
        add_tagged_image_1 = f"{additional_repo}:{tags[1]}"

        subprocess_popen.assert_has_calls(
            [
                call(["docker", "pull", tagged_image_0]),
                call(["docker", "pull", tagged_image_1]),
                call(["docker", "tag", tagged_image_0, add_tagged_image_0]),
                call(["docker", "push", add_tagged_image_0]),
                call(["docker", "tag", tagged_image_1, add_tagged_image_1]),
                call(["docker", "push", add_tagged_image_1]),
            ]
        )


@patch("subprocess.run")
def test_run_and_check_result_aborts_with_error_if_cli_command_errors(subprocess_run):
    subprocess_run.return_value = StubbedProcess(returncode=1, stderr="Things broke")

    with pytest.raises(Exception, match="Things broke"):
        run_and_check_result(["whatever"])
