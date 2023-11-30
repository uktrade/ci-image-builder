import os
from pathlib import Path
from test.doubles.process import StubbedProcess
from unittest.mock import patch

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from image_builder.codebase.revision import CodebaseRevisionMissingDataError
from image_builder.codebase.revision import CodebaseRevisionNoDataError
from image_builder.codebase.revision import load_codebase_revision


def git_revision_command(
    short_commit="shorthash",
    long_commit="longhash",
    branch: str | None = "main",
    repository="git@github.com:org/repo.git",
    tag: str | None = "2.0.0",
):
    def get_git_revision_data(command, shell=None, stdout=None):
        if command == "git rev-parse --short HEAD":
            return StubbedProcess(stdout=f"{short_commit}\n".encode())
        if command == "git rev-parse HEAD":
            return StubbedProcess(stdout=f"{long_commit}\n".encode())
        if command == "git show-ref --tags" and tag is not None:
            return StubbedProcess(
                stdout=f"longhash refs/tags/{tag}\notherhash refs/tags/1.0.0".encode()
            )
        if command == "git show-ref --heads" and branch is not None:
            return StubbedProcess(
                stdout=f"longhash refs/heads/{branch}\notherhash refs/heads/other".encode()
            )
        if command == "git ls-remote --get-url origin":
            return StubbedProcess(stdout=f"{repository}\n".encode())
        else:
            return StubbedProcess(stdout="".encode())

    return get_git_revision_data


class TestCodebaseRevision(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    @patch("subprocess.run", wraps=git_revision_command())
    def test_loading_revision_information(self, run):
        self.fs.create_dir(".git")
        revision = load_codebase_revision(Path("."))

        self.assertEqual(revision.commit, "shorthash")
        self.assertEqual(revision.branch, "main")
        self.assertEqual(revision.tag, "2.0.0")
        self.assertEqual(revision.get_repository_name(), "org/repo")
        self.assertEqual(revision.get_repository_url(), "https://github.com/org/repo")

    @patch(
        "subprocess.run",
        wraps=git_revision_command(repository="https://github.com/org/repo.git"),
    )
    def test_loading_revision_information_https_url(self, run):
        self.fs.create_dir(".git")
        revision = load_codebase_revision(Path("."))
        self.assertEqual(revision.get_repository_name(), "org/repo")
        self.assertEqual(revision.get_repository_url(), "https://github.com/org/repo")

    @patch(
        "subprocess.run", wraps=git_revision_command(branch="slash/separated/branch")
    )
    def test_loading_revision_information_slash_separated_branch(self, run):
        self.fs.create_dir(".git")
        revision = load_codebase_revision(Path("."))
        self.assertEqual(revision.branch, "slash/separated/branch")
        self.assertEqual(revision.get_repository_name(), "org/repo")
        self.assertEqual(revision.get_repository_url(), "https://github.com/org/repo")

    @patch("subprocess.run", wraps=git_revision_command(branch=None, tag=None))
    def test_loading_revision_information_codebuild_branch(self, run):
        self.fs.create_dir(".git")
        os.environ["CODEBUILD_WEBHOOK_TRIGGER"] = "branch/feat/tests"
        revision = load_codebase_revision(Path("."))
        self.assertEqual(revision.branch, "feat/tests")
        self.assertEqual(revision.tag, None)
        del os.environ["CODEBUILD_WEBHOOK_TRIGGER"]

    @patch("subprocess.run", wraps=git_revision_command(branch=None, tag=None))
    def test_loading_revision_information_codebuild_tag(self, run):
        self.fs.create_dir(".git")
        os.environ["CODEBUILD_WEBHOOK_TRIGGER"] = "tag/1.0.0"
        revision = load_codebase_revision(Path("."))
        self.assertEqual(revision.branch, None)
        self.assertEqual(revision.tag, "1.0.0")
        del os.environ["CODEBUILD_WEBHOOK_TRIGGER"]

    def test_loading_with_no_git_folder(self):
        with pytest.raises(CodebaseRevisionNoDataError):
            load_codebase_revision(Path("."))

    @patch(
        "subprocess.run",
        return_value=StubbedProcess(
            stdout=b"fatal: not a git repository (or any of the parent directories): .git",
            returncode=128,
        ),
    )
    def test_loading_with_no_git_information(self, run):
        self.fs.create_dir(".git")
        with pytest.raises(CodebaseRevisionMissingDataError):
            load_codebase_revision(Path("."))
