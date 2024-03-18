import stat
from pathlib import Path

from image_builder.codebase.language import Languages
from image_builder.codebase.language import load_codebase_languages
from image_builder.codebase.processes import Processes
from image_builder.codebase.processes import load_codebase_processes
from image_builder.codebase.revision import Revision
from image_builder.codebase.revision import load_codebase_revision
from image_builder.configuration.builder import load_builder_configuration
from image_builder.configuration.codebase import CodebaseConfiguration
from image_builder.configuration.codebase import load_codebase_configuration


class Codebase:
    build: CodebaseConfiguration
    path: Path
    revision: Revision
    processes: Processes
    languages: Languages
    original_files: dict

    def __init__(self, path: str | Path = None):
        self.path = Path(path)
        self.build = load_codebase_configuration(
            self.path.joinpath(".copilot/config.yml")
        )
        self.builder = load_builder_configuration()
        self.revision = load_codebase_revision(self.path)
        self.processes = load_codebase_processes(self.path)
        self.languages = load_codebase_languages(self.path)
        self.original_files = {
            "delete": {},
            "write": {},
        }

    def setup(self):
        self.builder.validate(self.build)
        self.original_files["write"]["Procfile"] = self.path.joinpath(
            "Procfile"
        ).read_text()
        self.processes.write()
        self.path.joinpath("buildpack-run.sh").write_text(
            Path(__file__).parent.joinpath("load_run_environment.sh").read_text()
        )
        self.path.joinpath("buildpack-run.sh").chmod(
            stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU
        )
        self.original_files["delete"]["buildpack-run.sh"] = None

        if self.build.packages:
            self.path.joinpath("Aptfile").write_text("\n".join(self.build.packages))
            self.original_files["delete"]["Aptfile"] = None

    def teardown(self):
        for filename, contents in self.original_files["write"].items():
            self.path.joinpath(filename).write_text(contents)
        for filename, contents in self.original_files["delete"].items():
            self.path.joinpath(filename).unlink()
