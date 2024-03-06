import os
import unittest
from pathlib import Path

import pytest
from parameterized import parameterized

from image_builder.configuration.builder import (BuilderSupport,
                                                 BuilderUnsupportedError,
                                                 load_builder_configuration)
from image_builder.configuration.codebase import load_codebase_configuration


class TestBuilderConfiguration(unittest.TestCase):
    @staticmethod
    def get_codebase_path(version: str):
        return (
            Path(__file__)
            .parent.parent.parent.joinpath(
                f"fixtures/codebase/{version}/.copilot/config.yml"
            )
            .resolve()
        )

    def setUp(self):
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

        self.builder_config_path = (
            Path(__file__)
            .parent.parent.parent.joinpath("fixtures/builder/config.yml")
            .resolve()
        )

    def test_loads_build_configurations(self):
        config = load_builder_configuration(self.builder_config_path)

        self.assertEqual(config.builders[0].name, "paketobuildpacks/builder-jammy-full")
        self.assertEqual(config.builders[0].deprecated, False)
        self.assertEqual(config.builders[0].versions[0].version, "0.3.288")

        self.assertEqual(config.builders[1].name, "paketobuildpacks/builder")
        self.assertEqual(config.builders[1].deprecated, True)
        self.assertEqual(config.builders[1].versions[0].version, "0.2.443-full")

    @parameterized.expand(
        [
            ("supported", BuilderSupport.SUPPORTED),
            ("deprecated", BuilderSupport.DEPRECATED),
        ]
    )
    def test_validates_codebase_configuration(self, codebase, expectation):
        builder_config = load_builder_configuration(self.builder_config_path)
        codebase_config = load_codebase_configuration(self.get_codebase_path(codebase))

        self.assertEqual(builder_config.validate(codebase_config), expectation)

    def test_validates_codebase_configuration_and_raises_unsupported_error(self):
        builder_config = load_builder_configuration(self.builder_config_path)
        codebase_config = load_codebase_configuration(
            self.get_codebase_path("unsupported")
        )

        with pytest.raises(BuilderUnsupportedError):
            builder_config.validate(codebase_config)
