import os
import subprocess
from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.codebase import load_codebase_languages_double
from test.doubles.codebase import load_codebase_processes_double
from test.doubles.codebase import load_codebase_revision_double
from unittest import mock
from unittest.mock import patch

from yaml import dump

from image_builder.codebase.codebase import Codebase
from image_builder.codebase.revision import Revision
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
                        "paketo-buildpacks/python",
                        "paketo-buildpacks/nodejs",
                    ],
                }
            ),
        )

        codebase = Codebase(Path("."))
        pack = Pack(codebase)

        self.assertEqual(
            pack.get_buildpacks(),
            [
                "fagiani/apt",
                "paketo-buildpacks/git",
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
                "fagiani/apt",
                "paketo-buildpacks/git",
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

    def test_get_repository_url_from_config(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack.repository, "000000000000.dkr.ecr.region.amazonaws.com/ecr/repos"
        )

    def test_get_public_repository_url_from_config(
        self,
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

        self.assertEqual(pack.repository, "public.ecr.aws/uktrade/repos")

    def test_get_repository_url_from_environment(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        os.environ["ECR_REPOSITORY"] = "ecr/environment-repo"
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack.repository,
            "000000000000.dkr.ecr.region.amazonaws.com/ecr/environment-repo",
        )

    def test_get_command(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack.get_command(),
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-latest "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-feat-tests "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env BPE_GIT_TAG=v2.4.6 "
            "--env BPE_GIT_COMMIT=shorthash "
            "--env BP_OCI_REVISION=shorthash "
            "--env BP_OCI_VERSION=shorthash "
            "--env BPE_GIT_BRANCH=feat/tests "
            "--env BP_OCI_REF_NAME=tag-v2.4.6 "
            "--env BP_OCI_SOURCE=https://github.com/org/repo "
            '--env BP_IMAGE_LABELS="uk.gov.trade.digital.build.timestamp=timestamp" '
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run "
            "--buildpack gcr.io/paketo-buildpacks/image-labels "
            "--buildpack gcr.io/paketo-buildpacks/environment-variables ",
        )

    def test_get_command_with_publish(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        self.assertEqual(
            pack.get_command(True),
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-latest "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-feat-tests "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env BPE_GIT_TAG=v2.4.6 "
            "--env BPE_GIT_COMMIT=shorthash "
            "--env BP_OCI_REVISION=shorthash "
            "--env BP_OCI_VERSION=shorthash "
            "--env BPE_GIT_BRANCH=feat/tests "
            "--env BP_OCI_REF_NAME=tag-v2.4.6 "
            "--env BP_OCI_SOURCE=https://github.com/org/repo "
            '--env BP_IMAGE_LABELS="uk.gov.trade.digital.build.timestamp=timestamp" '
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run "
            "--buildpack gcr.io/paketo-buildpacks/image-labels "
            "--buildpack gcr.io/paketo-buildpacks/environment-variables "
            "--publish --cache-image 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:cache",
        )

    def test_build(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase, "timestamp")

        pack.build()

        subprocess_popen.assert_called_with(
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-latest "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-feat-tests "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env BPE_GIT_TAG=v2.4.6 "
            "--env BPE_GIT_COMMIT=shorthash "
            "--env BP_OCI_REVISION=shorthash "
            "--env BP_OCI_VERSION=shorthash "
            "--env BPE_GIT_BRANCH=feat/tests "
            "--env BP_OCI_REF_NAME=tag-v2.4.6 "
            "--env BP_OCI_SOURCE=https://github.com/org/repo "
            '--env BP_IMAGE_LABELS="uk.gov.trade.digital.build.timestamp=timestamp" '
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run "
            "--buildpack gcr.io/paketo-buildpacks/image-labels "
            "--buildpack gcr.io/paketo-buildpacks/environment-variables ",
            shell=True,
            stdout=subprocess.PIPE,
        )
