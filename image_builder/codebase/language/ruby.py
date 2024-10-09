import re
from pathlib import Path

from .base import BaseLanguage
from .base import CodebaseLanguageNotDetectedError
from .end_of_life import get_latest_version_for


class RubyLanguage(BaseLanguage):
    name: str = "ruby"
    version: str

    @staticmethod
    def load(path: Path):
        has_ruby = path.joinpath("Gemfile").exists()
        if not has_ruby:
            raise CodebaseLanguageNotDetectedError

        language = RubyLanguage()

        if path.joinpath("Gemfile").exists():
            match = re.match(
                r"ruby[^\d]+([\d]+\.[\d]+)", path.joinpath("Gemfile").read_text()
            )

            if match is not None:
                version = match.group(1)
                language.version = f"{version}"

        if not hasattr(language, "version"):
            language.version = get_latest_version_for(language.name, False)

        return language
