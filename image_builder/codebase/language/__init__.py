from pathlib import Path

from .base import CodebaseLanguageError
from .nodejs import NodeJSLanguage
from .php import PHPLanguage
from .python import PythonLanguage
from .ruby import RubyLanguage

LANGUAGES = {
    "python": PythonLanguage,
    "nodejs": NodeJSLanguage,
    "ruby": RubyLanguage,
    "php": PHPLanguage,
}


class Languages(dict):
    def __str__(self):
        language_list = []
        for language in self.values():
            language_list.append(f"{language.name}@{language.version}")

        return ", ".join(language_list)


def load_codebase_languages(path: Path):
    languages = Languages()

    for language, language_class in LANGUAGES.items():
        try:
            languages[language] = language_class.load(path)
        except CodebaseLanguageError:
            pass

    return languages
