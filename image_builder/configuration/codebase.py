from pathlib import Path
from typing import List

from yaml import safe_load as yaml_load


class Builder:
    name: str
    version: str


class Pack:
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
        build.repository = config["repository"] if "repository" in config else None

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
