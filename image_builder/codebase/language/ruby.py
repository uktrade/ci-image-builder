import re
from pathlib import Path
from .base import BaseLanguage, CodebaseLanguageNotDetectedError


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

        return language
