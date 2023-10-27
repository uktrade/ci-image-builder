from pathlib import Path
from test.doubles.end_of_life import get_versions
from test.helpers.files import create_nodejs_indicator
from test.helpers.files import create_python_indicator
from unittest.mock import patch

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from image_builder.codebase.language import load_codebase_languages
from image_builder.codebase.language.base import BaseLanguage


class TestDetectingCodebaseLanguages(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    @patch("requests.get", wraps=get_versions)
    def test_only_python(self, requests_get):
        create_python_indicator(self.fs, "3.11.x", "runtime")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["python"].name, "python")
        self.assertEqual(languages["python"].version, "3.11")
        self.assertEqual(languages["python"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/python.json")

    @patch("requests.get", wraps=get_versions)
    def test_only_nodejs(self, requests_get):
        create_nodejs_indicator(self.fs, "18.4.2")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["nodejs"].name, "nodejs")
        self.assertEqual(languages["nodejs"].version, "18")
        self.assertEqual(languages["nodejs"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")

    @patch("requests.get", wraps=get_versions)
    def test_all_languages(self, requests_get):
        create_python_indicator(self.fs, "3.11.x", "runtime")
        create_nodejs_indicator(self.fs, "18.4.2")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["python"].name, "python")
        self.assertEqual(languages["python"].version, "3.11")
        self.assertEqual(languages["python"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/python.json")

        self.assertEqual(languages["nodejs"].name, "nodejs")
        self.assertEqual(languages["nodejs"].version, "18")
        self.assertEqual(languages["nodejs"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")


class TestBaseLanguageClass(TestCase):
    def test_load_is_not_implemented(self):
        class TestLanguage(BaseLanguage):
            pass

        with pytest.raises(NotImplementedError):
            TestLanguage.load(Path("."))
