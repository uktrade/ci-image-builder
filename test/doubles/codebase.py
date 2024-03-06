from image_builder.codebase.language import (Languages, NodeJSLanguage,
                                             PythonLanguage)
from image_builder.codebase.processes import Process, Processes
from image_builder.codebase.revision import Revision


def load_codebase_languages_double(path):
    languages = Languages()
    languages["python"] = PythonLanguage()
    languages["python"].version = "3.11"

    languages["nodejs"] = NodeJSLanguage()
    languages["nodejs"].version = "20.7"
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
        "git@github.com:org/repo.git", "shorthash", branch="feat/tests", tag="v2.4.6"
    )
