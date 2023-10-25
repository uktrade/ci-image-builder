from pathlib import Path

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from image_builder.codebase.processes import CodebaseProcessNoProcfileError
from image_builder.codebase.processes import load_codebase_processes


class TestCodebaseProcesses(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_without_procfile_present(self):
        with pytest.raises(CodebaseProcessNoProcfileError):
            load_codebase_processes(Path("."))

    def test_loading_simple_processes(self):
        self.fs.create_file(
            "Procfile",
            contents="web: cd src && python manage.py migrate --noinput && waitress-serve "
            "--port=$PORT --threads=6 config.wsgi:application",
        )

        processes = load_codebase_processes(Path("."))

        assert processes[0].name == "web"
        assert "cd src" in processes[0].commands
        assert "python manage.py migrate --noinput" in processes[0].commands
        assert (
            "waitress-serve --port=$PORT --threads=6 config.wsgi:application"
            in processes[0].commands
        )

    def test_loading_processes_and_filtering_write_commands(self):
        self.fs.create_file(
            "Procfile",
            contents="web: cd src && python manage.py collectstatic && waitress-serve "
            "--port=$PORT --threads=6 config.wsgi:application",
        )

        processes = load_codebase_processes(Path("."))

        assert processes[0].name == "web"
        assert "python manage.py collectstatic" not in processes[0].commands

    def test_processes_to_string(self):
        self.fs.create_file(
            "Procfile",
            contents="web: cd src && python manage.py migrate --noinput && python manage.py "
            "collectstatic && waitress-serve --port=$PORT --threads=6 "
            "config.wsgi:application",
        )

        processes = load_codebase_processes(Path("."))
        processes.write()

        assert Path("Procfile").read_text() == (
            "web: cd src && python manage.py migrate "
            "--noinput && waitress-serve --port=$PORT "
            "--threads=6 config.wsgi:application"
        )
