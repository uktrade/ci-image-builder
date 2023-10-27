from pathlib import Path
from typing import List


class CodebaseProcessError(Exception):
    pass


class CodebaseProcessNoProcfileError(CodebaseProcessError):
    pass


class Process:
    name: str
    commands: List[str]

    def __str__(self):
        commands = " && ".join(self.commands)
        return f"{self.name}: {commands}"


class Processes(List):
    path: Path

    def __init__(self, path):
        super().__init__()
        self.path = path

    def __str__(self):
        return "\n".join([str(p) for p in self])

    def write(self):
        self.path.write_text(str(self))


FILTER_COMMANDS = ["collectstatic"]


def load_codebase_processes(path: Path):
    if not path.joinpath("Procfile").exists():
        raise CodebaseProcessNoProcfileError

    processes = Processes(path.joinpath("Procfile"))

    procfile = path.joinpath("Procfile").read_text()

    for proc in procfile.split("\n"):
        line = proc.split(":")
        if line[0]:
            process = Process()
            process.name = line[0]
            commands = ":".join(line[1:])
            commands = commands.split("&&")
            commands = [c.strip() for c in commands]

            for filtered_command in FILTER_COMMANDS:
                commands = [c for c in commands if filtered_command not in c]

            process.commands = commands
            processes.append(process)

    return processes
