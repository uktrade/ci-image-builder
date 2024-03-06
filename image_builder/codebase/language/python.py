import re
import tomllib
from pathlib import Path

from .base import BaseLanguage, CodebaseLanguageNotDetectedError
from .end_of_life import get_latest_version_for


class PythonLanguage(BaseLanguage):
    name: str = "python"
    version: str

    @staticmethod
    def load(path: Path):
        has_python = (
            path.joinpath("requirements.txt").exists()
            or path.joinpath("pyproject.toml").exists()
            or (
                path.joinpath("runtime.txt").exists()
                and "python" in path.joinpath("runtime.txt").read_text()
            )
        )

        if not has_python:
            raise CodebaseLanguageNotDetectedError

        language = PythonLanguage()

        if path.joinpath("pyproject.toml").exists():
            try:
                pyproject = tomllib.loads(path.joinpath("pyproject.toml").read_text())
                version = re.search(
                    r"[0-9]+.[0-9]+",
                    pyproject["tool"]["poetry"]["dependencies"]["python"],
                )
                version = version.group(0)
                if version:
                    language.version = version
            except KeyError:
                pass

        if not hasattr(language, "version") and path.joinpath("runtime.txt").exists():
            version = re.search(
                r"[0-9]+.[0-9]+", path.joinpath("runtime.txt").read_text()
            )
            version = version.group(0)
            if version:
                language.version = version

        if not hasattr(language, "version"):
            language.version = get_latest_version_for(language.name, False)

        return language
