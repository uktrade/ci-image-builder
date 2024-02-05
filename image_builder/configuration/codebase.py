import os
from pathlib import Path
from typing import List

from yaml import safe_load as yaml_load

from image_builder.const import PUBLIC_REGISTRY


class Builder:
    name: str
    version: str


class Pack:
    # rename to BuildPack
    name: str


class CodebaseConfiguration:
    builder: Builder
    packs: List[Pack]
    repository: str
    packages: List[str]

    def __init__(self):
        self.builder = Builder()
        self.packs = []
        self.packages = []


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
        build.repository = get_repository(config)

        if "packs" in config:
            for pack_name in config["packs"]:
                pack = Pack()
                pack.name = pack_name
                build.packs.append(pack)

        if "packages" in config:
            build.packages = config["packages"]

        return build
    except FileNotFoundError as error:
        raise CodebaseConfigurationLoadError(f"file {error.filename} does not exist")
    except TypeError:
        raise CodebaseConfigurationLoadError(f"file is not valid")


def get_repository(config):
    codebuild_build_arn = os.getenv("CODEBUILD_BUILD_ARN")
    repository_from_environment = os.getenv("ECR_REPOSITORY")
    repository_from_config_file = config.get("repository")

    if repository_from_config_file and PUBLIC_REGISTRY in repository_from_config_file:
        return repository_from_config_file
    else:
        if not codebuild_build_arn:
            raise CodebaseConfigurationLoadError(
                f"codebuild build arn not set in environment variables"
            )

        if not repository_from_environment and not repository_from_config_file:
            raise CodebaseConfigurationLoadError(
                f"repository not set in config file or environment variables"
            )

        _, _, _, region, account, _, _ = codebuild_build_arn.split(":")
        return f"{account}.dkr.ecr.{region}.amazonaws.com/{repository_from_environment or repository_from_config_file}"
