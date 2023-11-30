import os
import re
import subprocess
from pathlib import Path


class CodebaseRevisionError(Exception):
    pass


class CodebaseRevisionNoDataError(CodebaseRevisionError):
    pass


class CodebaseRevisionMissingDataError(CodebaseRevisionError):
    pass


class Revision:
    remote: str
    branch: str
    commit: str
    tag: str

    def __init__(self, remote: str, commit: str, tag: str = None, branch: str = None):
        self.branch = branch
        self.commit = commit
        self.tag = tag
        self.remote = remote
        if not (self.remote or self.branch or self.tag):
            raise CodebaseRevisionMissingDataError

    def get_repository_name(self) -> str:
        match = re.search(r"([^:/.]+/[^:/.]+)(?:\.git)?$", self.remote)
        return match.group(1)

    def get_repository_url(self) -> str:
        return f"https://github.com/{self.get_repository_name()}"


def load_codebase_revision(path: Path):
    if not path.joinpath(".git").exists():
        raise CodebaseRevisionNoDataError

    commit = subprocess.run(
        "git rev-parse --short HEAD", shell=True, stdout=subprocess.PIPE
    )
    if commit.returncode == 0:
        commit = commit.stdout.strip().decode()
    else:
        commit = None

    branch = None

    long_commit = subprocess.run(
        "git rev-parse HEAD", shell=True, stdout=subprocess.PIPE
    )
    if long_commit.returncode == 0:
        long_commit = long_commit.stdout.strip().decode()
        branches = subprocess.run(
            "git show-ref --heads", shell=True, stdout=subprocess.PIPE
        )
        if branches.returncode == 0:
            branches = branches.stdout.strip().decode().split("\n")

            for possible_branch in branches:
                if possible_branch.startswith(long_commit):
                    branch = possible_branch.split(" ")[1]
                    branch = branch.replace("refs/heads/", "")
                    break

    if (
        branch is None
        and "CODEBUILD_WEBHOOK_TRIGGER" in os.environ
        and "branch" in os.environ["CODEBUILD_WEBHOOK_TRIGGER"]
    ):
        branch = os.environ["CODEBUILD_WEBHOOK_TRIGGER"].replace("branch/", "")

    tag = None

    long_commit = subprocess.run(
        "git rev-parse HEAD", shell=True, stdout=subprocess.PIPE
    )
    if long_commit.returncode == 0:
        long_commit = long_commit.stdout.strip().decode()
        tags = subprocess.run("git show-ref --tags", shell=True, stdout=subprocess.PIPE)
        if tags.returncode == 0:
            tags = tags.stdout.strip().decode().split("\n")

            for possible_tag in tags:
                if possible_tag.startswith(long_commit):
                    tag = possible_tag.split(" ")[1]
                    tag = tag.replace("refs/tags/", "")
                    break

    if (
        tag is None
        and "CODEBUILD_WEBHOOK_TRIGGER" in os.environ
        and "tag" in os.environ["CODEBUILD_WEBHOOK_TRIGGER"]
    ):
        tag = os.environ["CODEBUILD_WEBHOOK_TRIGGER"].replace("tag/", "")

    remote_url = subprocess.run(
        "git ls-remote --get-url origin", shell=True, stdout=subprocess.PIPE
    )
    if remote_url.returncode == 0:
        output = remote_url.stdout.strip().decode()
        remote = output if output else None
    else:
        remote = None

    return Revision(remote, commit, tag=tag, branch=branch)
