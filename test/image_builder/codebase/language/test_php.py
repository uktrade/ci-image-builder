from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.end_of_life import EndOfLifeResponse
from test.helpers.files import create_php_indicator
from unittest.mock import patch

import pytest
from parameterized import parameterized

from image_builder.codebase.language import PHPLanguage
from image_builder.codebase.language.base import CodebaseLanguageNotDetectedError


class TestCodebaseLanguagePHP(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()

    def test_without_php_application_present(self):
        with pytest.raises(CodebaseLanguageNotDetectedError):
            PHPLanguage.load(Path("."))

    @parameterized.expand(
        [
            ("8.3", "8.3"),
            (">=8.3", "8.3"),
            ("8.3.6", "8.3"),
            ("8.1", "8.1"),
            (">=8.1", "8.1"),
            ("8.1.8", "8.1"),
        ]
    )
    def test_getting_version_from_composer_json(self, input_version, output_version):
        create_php_indicator(self.fs, input_version)

        language = PHPLanguage.load(Path("."))

        assert language.name == "php"
        assert language.version == output_version

    @patch("requests.get", return_value=EndOfLifeResponse("php", 200))
    def test_getting_version_when_no_indicators_present(self, requests_get):
        self.fs.create_file("composer.json", contents="{}")

        language = PHPLanguage.load(Path("."))

        assert language.name == "php"
        assert language.version == "8.4"
