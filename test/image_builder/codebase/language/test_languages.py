from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.end_of_life import get_versions
from test.helpers.files import create_nodejs_indicator
from test.helpers.files import create_php_indicator
from test.helpers.files import create_python_indicator
from test.helpers.files import create_ruby_indicator
from unittest.mock import patch

import pytest

from image_builder.codebase.language import load_codebase_languages
from image_builder.codebase.language.base import BaseLanguage


class TestDetectingCodebaseLanguages(BaseTestCase):
    def setUp(self):
        super().setUp()
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
    def test_only_ruby(self, requests_get):
        create_ruby_indicator(self.fs, "3.3.2")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["ruby"].name, "ruby")
        self.assertEqual(languages["ruby"].version, "3.3")
        self.assertEqual(languages["ruby"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/ruby.json")

    @patch("requests.get", wraps=get_versions)
    def test_only_php(self, requests_get):
        create_php_indicator(self.fs, "8.3")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["php"].name, "php")
        self.assertEqual(languages["php"].version, "8.3")
        self.assertEqual(languages["php"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/php.json")

    @patch("requests.get", wraps=get_versions)
    def test_all_languages(self, requests_get):
        create_python_indicator(self.fs, "3.11.x", "runtime")
        create_nodejs_indicator(self.fs, "18.4.2")
        create_ruby_indicator(self.fs, "3.3.2")
        create_php_indicator(self.fs, "8.3.1")

        languages = load_codebase_languages(Path("."))

        self.assertEqual(languages["python"].name, "python")
        self.assertEqual(languages["python"].version, "3.11")
        self.assertEqual(languages["python"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/python.json")

        self.assertEqual(languages["nodejs"].name, "nodejs")
        self.assertEqual(languages["nodejs"].version, "18")
        self.assertEqual(languages["nodejs"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")

        self.assertEqual(languages["ruby"].name, "ruby")
        self.assertEqual(languages["ruby"].version, "3.3")
        self.assertEqual(languages["ruby"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/ruby.json")

        self.assertEqual(languages["php"].name, "php")
        self.assertEqual(languages["php"].version, "8.3")
        self.assertEqual(languages["php"].end_of_life, False)
        requests_get.assert_called_with("https://endoflife.date/api/php.json")


class TestBaseLanguageClass(BaseTestCase):
    def test_load_is_not_implemented(self):
        class TestLanguage(BaseLanguage):
            pass

        with pytest.raises(NotImplementedError):
            TestLanguage.load(Path("."))
