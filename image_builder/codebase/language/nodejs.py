import json
import re
from pathlib import Path

from .base import BaseLanguage, CodebaseLanguageNotDetectedError
from .end_of_life import get_latest_version_for


class NodeJSLanguage(BaseLanguage):
    name: str = "nodejs"
    version: str

    @staticmethod
    def load(path: Path):
        package_json = path.joinpath("package.json")

        if not package_json.exists():
            raise CodebaseLanguageNotDetectedError

        language = NodeJSLanguage()

        package_json = json.loads(package_json.read_text())

        if "engines" in package_json:
            if "node" in package_json["engines"]:
                version = re.search(
                    r"[0-9]+(.[0-9]+)?", package_json["engines"]["node"]
                )
                language.version = version.group(0)

        if hasattr(language, "version"):
            language.version = get_latest_version_for(
                language.name, False, language.version
            )
        else:
            language.version = get_latest_version_for(language.name, True)

        language.version = language.version.split(".")[0]

        return language
