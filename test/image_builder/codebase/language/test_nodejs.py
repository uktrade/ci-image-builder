import json
from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.end_of_life import get_versions
from test.helpers.files import create_nodejs_indicator
from unittest.mock import patch

import pytest
from parameterized import parameterized

from image_builder.codebase.language import NodeJSLanguage
from image_builder.codebase.language.base import CodebaseLanguageNotDetectedError


class TestCodebaseLanguageNodeJS(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()

    def test_without_nodejs_application_present(self):
        with pytest.raises(CodebaseLanguageNotDetectedError):
            NodeJSLanguage.load(Path("."))

    @patch("requests.get", wraps=get_versions)
    def test_with_nodejs_application_present(self, requests_get):
        create_nodejs_indicator(self.fs, "18.4.2")

        NodeJSLanguage.load(Path("."))

    @parameterized.expand(
        [
            (">18.10", "18", False),
            ("18", "18", False),
            ("19.4.33", "19", True),
            ("^20.4", "20", False),
        ]
    )
    @patch("requests.get", wraps=get_versions)
    def test_getting_nodejs_version_when_engines_present(
        self, input_version, output_version, eol, requests_get
    ):
        create_nodejs_indicator(self.fs, input_version)

        language = NodeJSLanguage.load(Path("."))

        self.assertEqual(language.name, "nodejs")
        self.assertEqual(language.version, output_version)
        self.assertEqual(language.end_of_life, eol)
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")

    @patch("requests.get", wraps=get_versions)
    def test_getting_nodejs_version_when_no_version_present(self, requests_get):
        self.fs.create_file("package.json", contents=json.dumps({}))

        language = NodeJSLanguage.load(Path("."))

        self.assertEqual(language.name, "nodejs")
        self.assertEqual(language.version, "20")
        self.assertEqual(language.end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")
