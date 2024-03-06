import os
from pathlib import Path
from typing import List

from yaml import safe_load as yaml_load

from image_builder.const import PUBLIC_REGISTRY
from image_builder.utils.arn_parser import ARN


class Builder:
    name: str
    version: str


class Buildpack:
    name: str


class CodebaseConfiguration:
    builder: Builder
    packs: List[Buildpack]
    registry: str
    repository_from_config_file: str
    packages: List[str]

    def __init__(self):
        self.builder = Builder()
        self.packs = []
        self.packages = []
        self.repository_from_config_file = ""

    @staticmethod
    def validate_build_arn(codebuild_build_arn):
        if not codebuild_build_arn:
            raise CodebaseConfigurationLoadError(
                f"codebuild build arn not set in environment variables"
            )

    @staticmethod
    def validate_ecr_config(repository_from_config_file, repository_from_environment):
        if not repository_from_environment and not repository_from_config_file:
            raise CodebaseConfigurationLoadError(
                f"Repository not set in config file or environment variables"
            )

    @property
    def repository(self):
        repository_from_environment = os.getenv("ECR_REPOSITORY")
        repository_from_config_file = self.repository_from_config_file

        self.validate_ecr_config(
            repository_from_config_file, repository_from_environment
        )

        repository = (
            repository_from_environment
            if repository_from_environment
            else repository_from_config_file
        )

        if PUBLIC_REGISTRY in repository:
            return repository

        codebuild_build_arn = os.getenv("CODEBUILD_BUILD_ARN")
        self.validate_build_arn(codebuild_build_arn)
        arn = ARN(codebuild_build_arn)

        return f"{arn.account_id}.dkr.ecr.{arn.region}.amazonaws.com/{repository}"

    @property
    def additional_repository(self):
        repository_from_environment = os.getenv("ECR_REPOSITORY")
        repository_from_config_file = self.repository_from_config_file

        self.validate_ecr_config(repository_from_config_file, repository_from_environment)

        repository = repository_from_environment if repository_from_environment else repository_from_config_file

        if PUBLIC_REGISTRY in repository:
            return repository

        codebuild_build_arn = os.getenv("CODEBUILD_BUILD_ARN")
        self.validate_build_arn(codebuild_build_arn)
        arn = ARN(codebuild_build_arn)

        return f"{arn.account_id}.dkr.ecr.{arn.region}.amazonaws.com/{repository}"

    @property
    def registry(self):
        return self.repository.split("/")[0]


class CodebaseConfigurationError(Exception):
    pass


class CodebaseConfigurationLoadError(CodebaseConfigurationError):
    pass


def load_codebase_configuration(path) -> CodebaseConfiguration:
    try:
        config = yaml_load(Path(path).read_text())
        build = CodebaseConfiguration()
        build.builder.name = config["builder"]["name"]
        build.builder.version = config["builder"]["version"]
        build.repository_from_config_file = config.get("repository")

        if "packs" in config:
            for pack_name in config["packs"]:
                pack = Buildpack()
                pack.name = pack_name
                build.packs.append(pack)

        if "packages" in config:
            build.packages = config["packages"]

        return build
    except FileNotFoundError as error:
        raise CodebaseConfigurationLoadError(f"file {error.filename} does not exist")
    except TypeError:
        raise CodebaseConfigurationLoadError(f"file is not valid")
