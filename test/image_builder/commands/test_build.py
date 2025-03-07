import os
import unittest
from pathlib import Path
from test.doubles.codebase import load_codebase_languages_double
from test.doubles.codebase import load_codebase_processes_double
from test.doubles.codebase import load_codebase_revision_double
from unittest.mock import ANY
from unittest.mock import call
from unittest.mock import patch

from click.testing import CliRunner

from image_builder.commands.build import build
from image_builder.const import ADDITIONAL_ECR_REPO
from image_builder.const import ECR_REPO


@patch("image_builder.commands.build.Progress")
@patch("image_builder.commands.build.Notify")
@patch("image_builder.commands.build.Codebase")
@patch("image_builder.commands.build.Docker")
@patch("image_builder.commands.build.Pack")
class TestBuildCommand(unittest.TestCase):
    @staticmethod
    def setup_mocks(pack, docker, codebase, notify, progress):
        os.environ[ECR_REPO] = "ecr/test-repository"
        os.environ.pop(ADDITIONAL_ECR_REPO, "")

        docker.running.return_value = True
        codebase().revision = load_codebase_revision_double(Path("."))
        codebase().processes = load_codebase_processes_double(Path("."))
        codebase().languages = load_codebase_languages_double(Path("."))
        codebase().build.builder.name = "test-builder"
        codebase().build.builder.version = "0000000"
        codebase().build.repository = "ecr/test-repository"
        codebase().get_notify_attrs.return_value = {
            "repository_name": "org/repo",
            "revision_commit": "commit-sha",
            "repository_url": "https://github.com/org/repo",
        }
        pack().get_buildpacks.return_value = [
            "fagiani/apt",
            "paketo-buildpacks/git",
            "paketo-buildpacks/python",
            "fagiani/run",
        ]

    @staticmethod
    def run_build(publish=False):
        runner = CliRunner()
        args = ["--send-notifications"]
        if publish:
            args.append("--publish")
        result = runner.invoke(build, args)
        return result

    def test_perfect_build(self, pack, docker, codebase, notify, progress):
        self.setup_mocks(pack, docker, codebase, notify, progress)
        result = self.run_build()

        self.assertIn("Docker is running, continuing with build...", result.output)
        self.assertIn(
            "Found revision: repository=org/repo, commit=shorthash, branch=feat/tests, "
            "tag=v2.4.6",
            result.output,
        )
        self.assertIn("Using ECR repository: ecr/test-repository", result.output)
        self.assertNotIn("Pushing image to additional ECR repository:", result.output)
        self.assertIn("Found processes: ['web']", result.output)
        self.assertIn("Found languages: python@3.11, nodejs@20.7", result.output)
        self.assertIn("Using builder: test-builder@0000000", result.output)
        self.assertIn(
            "Using buildpacks: ['fagiani/apt', 'paketo-buildpacks/git', "
            "'paketo-buildpacks/python', 'fagiani/run']",
            result.output,
        )

        pack().build.assert_called()
        pack().codebase.setup.assert_called()
        progress().set_current_phase.assert_has_calls([])
        notify().post_build_progress.assert_has_calls([call(ANY, ANY)] * 2)

    def test_perfect_build_with_publish_and_additional_repo(
        self, pack, docker, codebase, notify, progress
    ):
        additional_repo = "add/repo"
        codebase().build.additional_repository = additional_repo
        self.setup_mocks(pack, docker, codebase, notify, progress)
        result = self.run_build(publish=True)

        self.assertIn("Docker is running, continuing with build...", result.output)
        self.assertIn(
            "Found revision: repository=org/repo, commit=shorthash, branch=feat/tests, "
            "tag=v2.4.6",
            result.output,
        )
        self.assertIn("Using ECR repository: ecr/test-repository", result.output)
        self.assertIn(
            f"Pushing image to additional ECR repository: {additional_repo}",
            result.output,
        )
        self.assertIn("Found processes: ['web']", result.output)
        self.assertIn("Found languages: python@3.11, nodejs@20.7", result.output)
        self.assertIn("Using builder: test-builder@0000000", result.output)
        self.assertIn(
            "Using buildpacks: ['fagiani/apt', 'paketo-buildpacks/git', "
            "'paketo-buildpacks/python', 'fagiani/run']",
            result.output,
        )

        pack().build.assert_called()
        pack().codebase.setup.assert_called()
        progress().set_current_phase.assert_has_calls([])
        notify().post_build_progress.assert_has_calls([call(ANY, ANY)] * 2)

    @patch("click.secho")
    def test_when_setup_fails(
        self, mock_click, pack, docker, codebase, notify, progress
    ):
        self.setup_mocks(pack, docker, codebase, notify, progress)
        pack().codebase.setup.side_effect = ValueError("something went wrong!")
        result = self.run_build()

        pack().codebase.setup.assert_called()
        pack().build.assert_not_called()
        notify().post_build_progress.assert_has_calls([call(ANY, ANY)] * 2)
        self.assertEqual(result.exit_code, 1)
        mock_click.assert_called_with("Error: something went wrong!", fg="red")

    @patch("click.secho")
    def test_when_build_fails(
        self, mock_click, pack, docker, codebase, notify, progress
    ):
        self.setup_mocks(pack, docker, codebase, notify, progress)
        pack().build.side_effect = ValueError("something else went wrong!")
        result = self.run_build()

        pack().codebase.setup.assert_called()
        pack().build.assert_called()
        notify().post_build_progress.assert_has_calls([call(ANY, ANY)] * 2)
        self.assertEqual(result.exit_code, 1)
        mock_click.assert_called_with("Error: something else went wrong!", fg="red")

    @patch("click.secho")
    def test_when_user_aborts(
        self, mock_click, pack, docker, codebase, notify, progress
    ):
        self.setup_mocks(pack, docker, codebase, notify, progress)
        pack().build.side_effect = KeyboardInterrupt()
        result = self.run_build()

        pack().codebase.setup.assert_called()
        pack().build.assert_called()
        notify().post_build_progress.assert_has_calls([call(ANY, ANY)] * 2)
        notify().post_job_comment.assert_has_calls([call(ANY, ANY)])
        self.assertEqual(result.exit_code, 1)
        mock_click.assert_called_with("Build was cancelled: ", fg="red")

    def test_perfect_build_when_docker_is_not_started(
        self, pack, docker, codebase, notify, progress
    ):
        self.setup_mocks(pack, docker, codebase, notify, progress)
        docker.running.return_value = False
        self.run_build()
        docker.start.assert_called()
