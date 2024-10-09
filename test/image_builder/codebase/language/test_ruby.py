from pathlib import Path
from test.base_test_case import BaseTestCase
from test.helpers.files import create_ruby_indicator
from test.doubles.end_of_life import EndOfLifeResponse

import pytest
from unittest.mock import patch
from parameterized import parameterized

from image_builder.codebase.language import RubyLanguage
from image_builder.codebase.language.base import CodebaseLanguageNotDetectedError

class TestCodebaseLanguagePython(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()

    def test_without_ruby_application_present(self):
        with pytest.raises(CodebaseLanguageNotDetectedError):
            RubyLanguage.load(Path("."))


    @parameterized.expand(
        [
            ("\"3.2.1\"", "3.2"),
            ("\"3.3.4\"", "3.3"),
            ("\"3.3\"", "3.3"),
            ("'3.2.1'", "3.2"),
            (" '3.2.1'", "3.2"),
            ("\"3.3.x\"", "3.3"),
            ("\"3.11.8\"", "3.11"),
        ]
    )
    def test_getting_version_from_pyproject(self, input_version, output_version):
        create_ruby_indicator(self.fs, input_version)

        language = RubyLanguage.load(Path("."))

        assert language.name == "ruby"
        assert language.version == output_version

    @patch("requests.get", return_value=EndOfLifeResponse("ruby", 200))
    def test_getting_version_when_no_indicators_present(self, requests_get):
        self.fs.create_file("Gemfile", contents=f"")

        language = RubyLanguage.load(Path("."))

        assert language.name == "ruby"
        assert language.version == "3.3"
