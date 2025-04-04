from image_builder.codebase.language import Languages
from image_builder.codebase.language import NodeJSLanguage
from image_builder.codebase.language import PHPLanguage
from image_builder.codebase.language import PythonLanguage
from image_builder.codebase.language import RubyLanguage
from image_builder.codebase.processes import Process
from image_builder.codebase.processes import Processes
from image_builder.codebase.revision import Revision


def load_codebase_languages_double(path):
    languages = Languages()
    languages["python"] = PythonLanguage()
    languages["python"].version = "3.11"

    languages["nodejs"] = NodeJSLanguage()
    languages["nodejs"].version = "20.7"

    languages["ruby"] = RubyLanguage()
    languages["ruby"].version = "3.3"

    languages["php"] = PHPLanguage()
    languages["php"].version = "8.2"
    return languages


def load_codebase_processes_double(path):
    processes = Processes(path.joinpath("Procfile"))
    process = Process()
    process.name = "web"
    process.commands = ["django serve"]

    processes.append(process)
    return processes


def load_codebase_revision_double(path) -> Revision:
    return Revision(
        "git@github.com:org/repo.git",
        "shorthash",
        "longhash",
        branch="feat/tests",
        tag="v2.4.6",
    )
