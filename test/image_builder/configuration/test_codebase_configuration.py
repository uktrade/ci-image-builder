import os
import unittest
from pathlib import Path

import pytest

from image_builder.configuration.codebase import CodebaseConfiguration
from image_builder.configuration.codebase import CodebaseConfigurationLoadError


class TestCodebaseConfiguration(unittest.TestCase):
    def setUp(self):
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"
        os.environ["ECR_REPOSITORY"] = "some-repository"

    @staticmethod
    def get_codebase_path(version: str):
        return (
            Path(__file__)
            .parent.parent.parent.joinpath(
                f"fixtures/codebase/{version}/.copilot/config.yml"
            )
            .resolve()
        )

    def test_repository_with_no_repository_in_environment_variable_or_config_file(self):
        os.environ.pop("CODEBUILD_BUILD_ARN", None)
        os.environ.pop("ECR_REPOSITORY", None)
        config = CodebaseConfiguration()

        with pytest.raises(CodebaseConfigurationLoadError):
            config.repository

    def test_loading_a_codebase_configuration_with_repository_derived_from_environment_variables(
        self,
    ):
        config = CodebaseConfiguration()

        self.assertEqual(
            config.repository,
            "000000000000.dkr.ecr.region.amazonaws.com/some-repository",
        )

    def test_loading_a_codebase_configuration_with_repository_from_config_file(self):
        os.environ.pop("ECR_REPOSITORY", None)
        config = CodebaseConfiguration()
        config.repository_from_config_file = "ecr/repos"

        self.assertEqual(
            config.repository, "000000000000.dkr.ecr.region.amazonaws.com/ecr/repos"
        )

    def test_loading_a_codebase_configuration_with_public_repository_from_config_file(
        self,
    ):
        config = CodebaseConfiguration()
        config.repository_from_config_file = "public.ecr.aws/organisation/service"

        self.assertEqual(config.repository, "public.ecr.aws/organisation/service")

    def test_loading_a_codebase_configuration_environment_variables_overrides_private_repository_from_config_file(
        self,
    ):
        config = CodebaseConfiguration()
        config.repository_from_config_file = "ecr/repos"

        self.assertEqual(
            config.repository,
            f"000000000000.dkr.ecr.region.amazonaws.com/some-repository",
        )

    def test_loading_a_codebase_configuration_when_ecr_environment_variable_is_set_and_codebuild_arn_is_not_set(
        self,
    ):
        os.environ.pop("CODEBUILD_BUILD_ARN", None)
        config = CodebaseConfiguration()

        with pytest.raises(CodebaseConfigurationLoadError):
            config.repository

    def test_loading_a_codebase_configuration_sets_registry(self):
        config = CodebaseConfiguration()

        self.assertEqual(config.registry, "000000000000.dkr.ecr.region.amazonaws.com")
