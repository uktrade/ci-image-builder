import os
import subprocess
from pathlib import Path
from test.doubles.codebase import load_codebase_languages_double
from test.doubles.codebase import load_codebase_processes_double
from test.doubles.codebase import load_codebase_revision_double
from unittest.mock import patch

from pyfakefs.fake_filesystem_unittest import TestCase
from yaml import dump

from image_builder.codebase.codebase import Codebase
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
class TestPackBuildpacks(TestCase):
    def setUp(self):
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
class TestPackEnvironment(TestCase):
    def setUp(self):
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

    def test_environments(
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
            pack.get_environment(),
            [
                "BP_CPYTHON_VERSION=3.11",
                "BP_NODE_VERSION=20.7",
                "GIT_TAG=v2.4.6",
                "GIT_COMMIT=shorthash",
                "GIT_BRANCH=main",
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
class TestPackTags(TestCase):
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
            pack.get_tags(), ["commit-shorthash", "tag-v2.4.6", "branch-main"]
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
class TestCommand(TestCase):
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

    def test_get_command(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase)
        self.assertEqual(
            pack.get_command(),
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-main "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env GIT_TAG=v2.4.6 "
            "--env GIT_COMMIT=shorthash "
            "--env GIT_BRANCH=main "
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run ",
        )

    def test_get_command_with_publish(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase)
        self.assertEqual(
            pack.get_command(True),
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-main "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env GIT_TAG=v2.4.6 "
            "--env GIT_COMMIT=shorthash "
            "--env GIT_BRANCH=main "
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run "
            "--publish --cache-image 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos-cache",
        )

    def test_build(
        self,
        subprocess_popen,
        load_codebase_revision,
        load_codebase_processes,
        load_codebase_languages,
    ):
        codebase = Codebase(Path("."))
        pack = Pack(codebase)
        pack.build()
        subprocess_popen.assert_called_with(
            "pack build 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos "
            "--builder paketobuildpacks/builder-jammy-full:0.3.288 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:commit-shorthash "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:tag-v2.4.6 "
            "--tag 000000000000.dkr.ecr.region.amazonaws.com/ecr/repos:branch-main "
            "--env BP_CPYTHON_VERSION=3.11 "
            "--env BP_NODE_VERSION=20.7 "
            "--env GIT_TAG=v2.4.6 "
            "--env GIT_COMMIT=shorthash "
            "--env GIT_BRANCH=main "
            "--buildpack fagiani/apt "
            "--buildpack paketo-buildpacks/git "
            "--buildpack paketo-buildpacks/python "
            "--buildpack paketo-buildpacks/nodejs "
            "--buildpack fagiani/run ",
            shell=True,
            stdout=subprocess.PIPE,
        )
