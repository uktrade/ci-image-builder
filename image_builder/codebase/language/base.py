from pathlib import Path

from image_builder.codebase.language.end_of_life import is_end_of_life


class CodebaseLanguageError(Exception):
    pass


class CodebaseLanguageNotDetectedError(CodebaseLanguageError):
    pass


class BaseLanguage:
    name: str
    version: str

    @property
    def end_of_life(self):
        return is_end_of_life(self.name, self.version)

    @staticmethod
    def load(path: Path):
        raise NotImplementedError
