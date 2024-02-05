from pathlib import Path
from test.doubles.end_of_life import EndOfLifeResponse
from test.helpers.files import create_python_indicator
from unittest.mock import patch

import pytest
from parameterized import parameterized

from image_builder.codebase.language import PythonLanguage
from image_builder.codebase.language.base import CodebaseLanguageNotDetectedError


class TestCodebaseLanguagePython(BaseTestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_without_python_application_present(self):
        with pytest.raises(CodebaseLanguageNotDetectedError):
            PythonLanguage.load(Path("."))

    @parameterized.expand(
        [
            ("3.9", "3.9"),
            ("^3.9", "3.9"),
            ("3.9.5", "3.9"),
            ("3.10", "3.10"),
            ("3.10.6", "3.10"),
            ("^3.10.6", "3.10"),
            ("3.11", "3.11"),
            ("^3.11", "3.11"),
            ("3.11.8", "3.11"),
            ("3.12.1", "3.12"),
        ]
    )
    def test_getting_version_from_pyproject(self, input_version, output_version):
        create_python_indicator(self.fs, input_version)

        language = PythonLanguage.load(Path("."))

        assert language.name == "python"
        assert language.version == output_version

    @parameterized.expand(
        [
            ("3.9", "3.9"),
            ("3.9.x", "3.9"),
            ("3.9.5", "3.9"),
            ("3.10", "3.10"),
            ("3.10.6", "3.10"),
            ("3.10.x", "3.10"),
            ("3.11", "3.11"),
            ("3.11.x", "3.11"),
            ("3.11.8", "3.11"),
        ]
    )
    def test_getting_version_from_runtime(self, input_version, output_version):
        create_python_indicator(self.fs, input_version, "runtime")

        language = PythonLanguage.load(Path("."))

        assert language.name == "python"
        assert language.version == output_version

    @patch("requests.get", return_value=EndOfLifeResponse("python", 200))
    def test_getting_version_when_no_indicators_present(self, requests_get):
        self.fs.create_file("pyproject.toml", contents=f"")

        language = PythonLanguage.load(Path("."))

        assert language.name == "python"
        assert language.version == "3.12"
