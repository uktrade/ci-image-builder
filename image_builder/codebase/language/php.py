import json
import re
from pathlib import Path

from .base import BaseLanguage
from .base import CodebaseLanguageNotDetectedError
from .end_of_life import get_latest_version_for


class PHPLanguage(BaseLanguage):
    name: str = "php"
    version: str

    @staticmethod
    def load(path: Path):
        composer_json = path.joinpath("composer.json")

        if not composer_json.exists():
            raise CodebaseLanguageNotDetectedError

        language = PHPLanguage()

        composer_json = json.loads(composer_json.read_text())

        if "require" in composer_json:
            if "php" in composer_json["require"]:
                version = re.search(
                    r"[0-9]+(.[0-9]+)?", composer_json["require"]["php"]
                )
                language.version = version.group(0)

        if hasattr(language, "version"):
            language.version = get_latest_version_for(
                language.name, False, language.version
            )
        else:
            language.version = get_latest_version_for(language.name, False)

        return language
