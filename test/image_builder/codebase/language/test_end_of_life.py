import unittest
from test.doubles.end_of_life import get_versions
from unittest.mock import patch

import pytest

from image_builder.codebase.language import end_of_life
from image_builder.codebase.language.end_of_life import is_end_of_life


class TestEndOfLifeLatestVersion(unittest.TestCase):
    @patch("requests.get", wraps=get_versions)
    def test_when_there_is_no_data_for_a_product(self, requests_get):
        with pytest.raises(end_of_life.EndOfLifeNoProductError):
            end_of_life.get_latest_version_for("not-a-product")

        requests_get.assert_called_with("https://endoflife.date/api/not-a-product.json")

    @patch("requests.get", wraps=get_versions)
    def test_when_a_product_exists(self, requests_get):
        version = end_of_life.get_latest_version_for("nodejs")

        self.assertEqual(version, "20.8")
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")

    @patch("requests.get", wraps=get_versions)
    def test_when_looking_for_non_lts_versions(self, requests_get):
        version = end_of_life.get_latest_version_for("nodejs", False)

        self.assertEqual(version, "21.0")
        requests_get.assert_called_with("https://endoflife.date/api/nodejs.json")

    @patch("requests.get", wraps=get_versions)
    def test_when_looking_for_specific_versions(self, requests_get):
        version = end_of_life.get_latest_version_for("python", False, "3.11")

        self.assertEqual(version, "3.11")
        requests_get.assert_called_with("https://endoflife.date/api/python.json")


class TestEndOfLifeVersionIsEndOfLife(unittest.TestCase):
    @patch("requests.get", wraps=get_versions)
    def test_when_a_version_is_end_of_life_with_a_date(self, requests_get):
        self.assertEqual(is_end_of_life("python", "2.6"), True)

    @patch("requests.get", wraps=get_versions)
    def test_when_a_version_is_end_of_life(self, requests_get):
        self.assertEqual(is_end_of_life("nodejs", "2.3"), True)

    @patch("requests.get", wraps=get_versions)
    def test_when_a_version_is_not_end_of_life(self, requests_get):
        self.assertEqual(is_end_of_life("python", "3.11"), False)
