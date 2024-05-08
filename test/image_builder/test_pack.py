import os
import subprocess
from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.codebase import load_codebase_languages_double
from test.doubles.codebase import load_codebase_processes_double
from test.doubles.codebase import load_codebase_revision_double
from unittest import mock
from unittest.mock import patch

from parameterized import parameterized
from yaml import dump

from image_builder.codebase.codebase import Codebase
from image_builder.codebase.revision import Revision
from image_builder.const import ADDITIONAL_ECR_REPO
from image_builder.const import ECR_REPO
from image_builder.pack import Pack


@patch(
    "image_builder.codebase.codebase.load_codebase_languages",
    wraps=load_codebase_languages_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_processes",
    wraps=load_codebase_processes_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_revision",
    wraps=load_codebase_revision_double,
)
class TestPackBuildpacks(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

        self.setUpPyfakefs()
        self.fs.add_real_paths(
            [
                Path(__file__)
                .parent.parent.parent.joinpath(
                    "image_builder/configuration/builder_configuration.yml"
                )
                .resolve()
            ]
        )

    def test_buildpacks_when_present_in_config(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                    "packs": [
                        "paketo-buildpacks/nginx",
                    ],
                }
            ),
        )

        codebase = Codebase(Path("."))
        pack = Pack(codebase)

        self.assertEqual(
            pack.get_buildpacks(),
            [
                "paketo-buildpacks/git",
                "paketo-buildpacks/nginx",
                "paketo-buildpacks/python",
                "paketo-buildpacks/nodejs",
                "fagiani/run",
                "gcr.io/paketo-buildpacks/image-labels",
                "gcr.io/paketo-buildpacks/environment-variables",
            ],
        )

    def test_buildpacks_when_not_present_in_config(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                }
            ),
        )

        codebase = Codebase(Path("."))
        pack = Pack(codebase)

        self.assertEqual(
            pack.get_buildpacks(),
            [
                "paketo-buildpacks/git",
                "paketo-buildpacks/python",
                "paketo-buildpacks/nodejs",
                "fagiani/run",
                "gcr.io/paketo-buildpacks/image-labels",
                "gcr.io/paketo-buildpacks/environment-variables",
            ],
        )

    def test_buildpacks_when_packages_present_in_config(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                    "packages": [
                        "graphviz",
                    ],
                }
            ),
        )

        codebase = Codebase(Path("."))
        pack = Pack(codebase)

        self.assertEqual(
            pack.get_buildpacks(),
            [
                "paketo-buildpacks/git",
                "fagiani/apt",
                "paketo-buildpacks/python",
                "paketo-buildpacks/nodejs",
                "fagiani/run",
                "gcr.io/paketo-buildpacks/image-labels",
                "gcr.io/paketo-buildpacks/environment-variables",
            ],
        )


@patch(
    "image_builder.codebase.codebase.load_codebase_languages",
    wraps=load_codebase_languages_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_processes",
    wraps=load_codebase_processes_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_revision",
    wraps=load_codebase_revision_double,
)
class TestPackEnvironment(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

        self.setUpPyfakefs()
        self.fs.add_real_paths(
            [
                Path(__file__)
                .parent.parent.parent.joinpath(
                    "image_builder/configuration/builder_configuration.yml"
                )
                .resolve()
            ]
        )
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                }
            ),
        )

    def test_get_environment(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        environment = pack.get_environment()

        self.assertEqual(
            environment,
            [
                "BP_CPYTHON_VERSION=3.11",
                "BP_NODE_VERSION=20.7",
                "BPE_GIT_TAG=v2.4.6",
                "BPE_GIT_COMMIT=shorthash",
                "BP_OCI_REVISION=shorthash",
                "BP_OCI_VERSION=shorthash",
                "BPE_GIT_BRANCH=feat/tests",
                "BP_OCI_REF_NAME=tag-v2.4.6",
                "BP_OCI_SOURCE=https://github.com/org/repo",
                'BP_IMAGE_LABELS="uk.gov.trade.digital.build.timestamp=timestamp"',
            ],
        )

    def test_get_environment_with_tagged_commit_sets_bp_oci_ref_name_to_tag(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        environment = pack.get_environment()

        self.assertIn("BP_OCI_REF_NAME=tag-v2.4.6", environment)

    def test_get_environment_with_untagged_commit_sets_bp_oci_ref_name_to_commit(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        # Override load_codebase_revision to return a Revision with a tag
        with mock.patch(
            "image_builder.codebase.codebase.load_codebase_revision",
            mock.Mock(
                return_value=Revision(
                    "git@github.com:org/repo.git", "shorthash", branch="feat/tests"
                )
            ),
        ):
            codebase = Codebase(Path("."))
            pack = Pack(codebase, "timestamp")

            environment = pack.get_environment()

            self.assertIn("BP_OCI_REF_NAME=commit-shorthash", environment)


@patch(
    "image_builder.codebase.codebase.load_codebase_languages",
    wraps=load_codebase_languages_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_processes",
    wraps=load_codebase_processes_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_revision",
    wraps=load_codebase_revision_double,
)
class TestPackTags(BaseTestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                }
            ),
        )
        self.fs.add_real_paths(
            [
                Path(__file__)
                .parent.parent.parent.joinpath(
                    "image_builder/configuration/builder_configuration.yml"
                )
                .resolve()
            ]
        )

    def test_get_tags(
        self, load_codebase_revision, load_codebase_processes, load_codebase_languages
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase)

        self.assertEqual(
            pack.get_tags(),
            ["commit-shorthash", "tag-v2.4.6", "tag-latest", "branch-feat-tests"],
        )


@patch(
    "image_builder.codebase.codebase.load_codebase_languages",
    wraps=load_codebase_languages_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_processes",
    wraps=load_codebase_processes_double,
)
@patch(
    "image_builder.codebase.codebase.load_codebase_revision",
    wraps=load_codebase_revision_double,
)
@patch(
    "subprocess.Popen",
    return_value=subprocess.Popen(
        f"bash {Path(__file__).parent.parent.joinpath('doubles/fake_pack.sh').resolve()}",
        shell=True,
        stdout=subprocess.PIPE,
    ),
)
@patch("image_builder.pack.publish_to_additional_repository")
class TestCommand(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.setUpPyfakefs()
        self.fs.create_dir(".copilot")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "ecr/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                }
            ),
        )
        self.fs.create_file(".copilot/post_image_build.sh")
        self.fs.add_real_paths(
            [
                Path(__file__)
                .parent.parent.parent.joinpath(
                    "image_builder/configuration/builder_configuration.yml"
                )
                .resolve()
            ]
        )
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

        self.expected_tags = [
            "commit-shorthash",
            "tag-v2.4.6",
            "tag-latest",
            "branch-feat-tests",
        ]
        self.expected_command = [
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos",
            "--builder paketobuildpacks/builder-jammy-full:0.3.288",
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash",
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6",
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-latest",
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-feat-tests",
            "--env BP_CPYTHON_VERSION=3.11",
            "--env BP_NODE_VERSION=20.7",
            "--env BPE_GIT_TAG=v2.4.6",
            "--env BPE_GIT_COMMIT=shorthash",
            "--env BP_OCI_REVISION=shorthash",
            "--env BP_OCI_VERSION=shorthash",
            "--env BPE_GIT_BRANCH=feat/tests",
            "--env BP_OCI_REF_NAME=tag-v2.4.6",
            "--env BP_OCI_SOURCE=https://github.com/org/repo",
            '--env BP_IMAGE_LABELS="uk.gov.trade.digital.build.timestamp=timestamp"',
            "--buildpack paketo-buildpacks/git",
            "--buildpack paketo-buildpacks/python",
            "--buildpack paketo-buildpacks/nodejs",
            "--buildpack fagiani/run",
            "--buildpack gcr.io/paketo-buildpacks/image-labels",
            "--buildpack gcr.io/paketo-buildpacks/environment-variables",
        ]
        self.publish_opts = "--publish --cache-image 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:cache"

    def test_get_repository_url_from_config(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack._repository, "000000000000.dkr.ecr.region.amazonaws.com/ecr/repos"
        )

    def test_get_public_repository_url_from_config(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        # Replace the original repository in the config
        # with a public one
        self.fs.remove(".copilot/config.yml")
        self.fs.create_file(
            ".copilot/config.yml",
            contents=dump(
                {
                    "repository": "public.ecr.aws/uktrade/repos",
                    "builder": {
                        "name": "paketobuildpacks/builder-jammy-full",
                        "version": "0.3.288",
                    },
                }
            ),
        )

        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(pack._repository, "public.ecr.aws/uktrade/repos")

    def test_get_repository_url_from_environment(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        os.environ[ECR_REPO] = "ecr/environment-repo"
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack._repository,
            "000000000000.dkr.ecr.region.amazonaws.com/ecr/environment-repo",
        )

    def test_get_command(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(pack.get_command(), " ".join(self.expected_command))

    def test_get_command_with_publish(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        expected = " ".join(self.expected_command + [self.publish_opts])

        self.assertEqual(pack.get_command(True), expected)

    def test_build(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        pack.build()

        subprocess_popen.assert_called_with(
            " ".join(self.expected_command),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    @parameterized.expand(
        [
            ("ecr/repo2", "000000000000.dkr.ecr.region.amazonaws.com/ecr/repo2"),
            ("public.ecr.aws/my/repo", "public.ecr.aws/my/repo"),
        ]
    )
    def test_build_and_publish_to_additional_repo(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
        additional_repository,
        exp_additional_repository,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")
        os.environ[ADDITIONAL_ECR_REPO] = additional_repository
        exp_initial_repo = "000000000000.dkr.ecr.region.amazonaws.com/ecr/repos"

        pack.build(publish=True)

        expected = " ".join(self.expected_command + [self.publish_opts])
        subprocess_popen.assert_called_with(
            expected,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        publish_to_additional.assert_called_with(
            exp_initial_repo, exp_additional_repository, self.expected_tags
        )

    def test_build_without_publish_does_not_publish_to_additional_repo(
        self,
        publish_to_additional,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")
        os.environ[ADDITIONAL_ECR_REPO] = "public.ecr.aws/my/repo"

        pack.build(publish=False)

        expected = " ".join(self.expected_command)
        subprocess_popen.assert_called_with(
            expected,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        publish_to_additional.assert_not_called()
