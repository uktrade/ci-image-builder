import unittest
from pathlib import Path

import pytest

from image_builder.configuration.codebase import CodebaseConfigurationLoadError
from image_builder.configuration.codebase import load_codebase_configuration


class TestSupportedBuildConfiguration(unittest.TestCase):
    @staticmethod
    def get_codebase_path(version: str):
        return (
            Path(__file__)
            .parent.parent.parent.joinpath(
                f"fixtures/codebase/{version}/.copilot/config.yml"
            )
            .resolve()
        )

    def test_loading_a_valid_codebase_configuration(self):
        config = load_codebase_configuration(self.get_codebase_path("supported"))

        self.assertEqual(config.builder.name, "paketobuildpacks/builder-jammy-full")
        self.assertEqual(config.builder.version, "0.3.288")
        self.assertEqual(config.packs[0].name, "paketo-buildpacks/python")
        self.assertEqual(config.packs[1].name, "paketo-buildpacks/nodejs")

    def test_loading_an_invalid_codebase_configuration(self):
        with pytest.raises(CodebaseConfigurationLoadError):
            load_codebase_configuration(self.get_codebase_path("invalid"))

    def test_loading_a_missing_codebase_configuration(self):
        with pytest.raises(CodebaseConfigurationLoadError):
            load_codebase_configuration(self.get_codebase_path("missing"))