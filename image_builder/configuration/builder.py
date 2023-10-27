from enum import Enum
from pathlib import Path
from typing import List

from yaml import safe_load as yaml_load

from image_builder.configuration.codebase import CodebaseConfiguration


class BuilderError(Exception):
    pass


class BuilderUnsupportedError(BuilderError):
    pass


class BuilderSupport(Enum):
    SUPPORTED = 1
    DEPRECATED = 2
    UNSUPPORTED = 3


class BuilderVersion:
    version: str
    deprecated: bool


class Builder:
    name: str
    deprecated: bool
    versions: List[BuilderVersion]

    def __init__(self):
        self.versions = []


class BuilderConfiguration:
    builders: List[Builder]

    def __init__(self):
        self.builders = []

    def validate(self, codebase: CodebaseConfiguration):
        found_builder_name = False
        deprecated_builder_name = False
        found_builder_version = False
        deprecated_builder_version = False

        for builder in self.builders:
            if builder.name == codebase.builder.name:
                found_builder_name = True

                if builder.deprecated:
                    deprecated_builder_name = True

            for builder_version in builder.versions:
                if builder_version.version == codebase.builder.version:
                    found_builder_version = True

                    if builder_version.deprecated:
                        deprecated_builder_version = True

        if found_builder_name and found_builder_version:
            if deprecated_builder_name or deprecated_builder_version:
                return BuilderSupport.DEPRECATED

            return BuilderSupport.SUPPORTED

        raise BuilderUnsupportedError(
            f"Builder {codebase.builder.name}@{codebase.builder.version} "
            f"not supported."
        )


def load_builder_configuration(path: Path = None) -> BuilderConfiguration:
    if not path:
        path = Path(__file__).parent.joinpath("builder_configuration.yml")

    config_raw = path.read_text()
    config_parsed = yaml_load(config_raw)
    builder_configuration = BuilderConfiguration()
    for builder_config in config_parsed["builders"]:
        builder = Builder()
        builder.name = builder_config["name"]
        builder.deprecated = (
            builder_config["deprecated"] if ("deprecated" in builder_config) else False
        )

        for version_config in builder_config["versions"]:
            version = BuilderVersion()
            version.version = version_config["version"]
            version.deprecated = (
                version_config["deprecated"]
                if ("deprecated" in version_config)
                else builder_config["deprecated"]
                if ("deprecated" in builder_config)
                else False
            )
            builder.versions.append(version)

        builder_configuration.builders.append(builder)

    return builder_configuration
