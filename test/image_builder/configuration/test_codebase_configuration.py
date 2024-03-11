import os
import unittest
from pathlib import Path

import pytest
from parameterized import parameterized

from image_builder.configuration.codebase import CodebaseConfiguration
from image_builder.configuration.codebase import CodebaseConfigurationLoadError
from image_builder.const import ADDITIONAL_ECR_REPO
from image_builder.const import ECR_REPO


class TestCodebaseConfiguration(unittest.TestCase):
    def setUp(self):
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"
        os.environ[ECR_REPO] = "some-repository"

    def tearDown(self) -> None:
        if ECR_REPO in os.environ:
            del os.environ[ECR_REPO]
        if ADDITIONAL_ECR_REPO in os.environ:
            del os.environ[ADDITIONAL_ECR_REPO]

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
        os.environ.pop(ECR_REPO, None)
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
        os.environ.pop(ECR_REPO, None)
        config = CodebaseConfiguration()
        config.repository_from_config_file = "ecr/repos"

        self.assertEqual(
            config.repository, "000000000000.dkr.ecr.region.amazonaws.com/ecr/repos"
        )

    @parameterized.expand(
        [
            (
                "public.ecr.aws/org/repo_1",
                "private/repo_1",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_1",
            ),
            (
                "private/repo_2",
                "public.ecr.aws/org/repo_2",
                "public.ecr.aws/org/repo_2",
            ),
            (
                "public.ecr.aws/org/repo_3",
                "public.ecr.aws/org/repo_4",
                "public.ecr.aws/org/repo_4",
            ),
            (
                "private/repo_3",
                "private/repo_4",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_4",
            ),
        ]
    )
    def test_loading_repository_env_var_overrides_config(
        self, config_repo, env_repo, expected
    ):
        config = CodebaseConfiguration()
        config.repository_from_config_file = config_repo
        os.environ[ECR_REPO] = env_repo

        self.assertEqual(config.repository, expected)

    @parameterized.expand(
        [
            ("public.ecr.aws/org/repo_1", "public.ecr.aws/org/repo_1"),
            (
                "private/repo_3",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_3",
            ),
        ]
    )
    def test_loading_repository_from_config_formats_are_correct(
        self, config_repo, expected
    ):
        config = CodebaseConfiguration()
        config.repository_from_config_file = config_repo
        del os.environ[ECR_REPO]

        self.assertEqual(config.repository, expected)

    @parameterized.expand(
        [
            ("public.ecr.aws/org/repo_1", "public.ecr.aws/org/repo_1"),
            (
                "private/repo_3",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_3",
            ),
        ]
    )
    def test_loading_repository_from_env_var_formats_are_correct(
        self, env_var, expected
    ):
        config = CodebaseConfiguration()
        config.repository_from_config_file = None
        os.environ[ECR_REPO] = env_var

        self.assertEqual(config.repository, expected)

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

    @parameterized.expand(
        [
            (
                "public.ecr.aws/org/repo_1",
                "private/repo_1",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_1",
            ),
            (
                "private/repo_2",
                "public.ecr.aws/org/repo_2",
                "public.ecr.aws/org/repo_2",
            ),
            (
                "public.ecr.aws/org/repo_3",
                "public.ecr.aws/org/repo_4",
                "public.ecr.aws/org/repo_4",
            ),
            (
                "private/repo_3",
                "private/repo_4",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_4",
            ),
        ]
    )
    def test_loading_additional_repository_env_var_overrides_config(
        self, config_repo, env_repo, expected
    ):
        config = CodebaseConfiguration()
        config.additional_repository_from_config_file = config_repo
        os.environ[ADDITIONAL_ECR_REPO] = env_repo

        self.assertEqual(config.additional_repository, expected)

    @parameterized.expand(
        [
            ("public.ecr.aws/org/repo_1", "public.ecr.aws/org/repo_1"),
            (
                "private/repo_3",
                "000000000000.dkr.ecr.region.amazonaws.com/private/repo_3",
            ),
        ]
    )
    def test_loading_additional_repository_from_config_formats_are_correct(
        self, config_repo, expected
    ):
        config = CodebaseConfiguration()
        config.additional_repository_from_config_file = config_repo

        self.assertEqual(config.additional_repository, expected)

    def test_no_additional_repository_configured(self):
        config = CodebaseConfiguration()
        config.additional_repository_from_config_file = None

        self.assertEqual(config.additional_repository, None)

    def test_additional_private_repository_with_missing_codebuild_arn_fails(self):
        del os.environ["CODEBUILD_BUILD_ARN"]
        config = CodebaseConfiguration()
        config.additional_repository_from_config_file = "private/repo"

        with pytest.raises(CodebaseConfigurationLoadError):
            config.additional_repository
