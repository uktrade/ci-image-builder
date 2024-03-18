import os
from pathlib import Path
from test.base_test_case import BaseTestCase
from test.doubles.codebase import load_codebase_languages_double
from test.doubles.codebase import load_codebase_processes_double
from test.doubles.codebase import load_codebase_revision_double
from unittest.mock import patch

from yaml import dump

from image_builder.codebase.codebase import Codebase


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
class TestCodebase(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ[
            "CODEBUILD_BUILD_ARN"
        ] = "arn:aws:codebuild:region:000000000000:build/project:example-build-id"

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
        self.fs.create_file(
            "Procfile", contents="web: django collectstatic && django serve"
        )
        self.fs.add_real_paths(
            [
                Path(__file__)
                .parent.parent.parent.parent.joinpath(
                    "image_builder/configuration/builder_configuration.yml"
                )
                .resolve(),
                Path(__file__)
                .parent.parent.parent.parent.joinpath(
                    "image_builder/codebase/load_run_environment.sh"
                )
                .resolve(),
            ],
        )

    def test_loading_codebase(
        self, load_codebase_revision, load_codebase_processes, get_codebase_languages
    ):
        codebase = Codebase(Path("."))

        load_codebase_revision.assert_called_with(Path("."))
        load_codebase_processes.assert_called_with(Path("."))
        get_codebase_languages.assert_called_with(Path("."))

        self.assertEqual(codebase.revision.commit, "shorthash")
        self.assertEqual(codebase.revision.branch, "feat/tests")
        self.assertEqual(codebase.revision.tag, "v2.4.6")

        self.assertEqual(codebase.languages["python"].version, "3.11")
        self.assertEqual(codebase.processes[0].name, "web")
        self.assertEqual(codebase.processes[0].commands, ["django serve"])

    def test_codebase_setup(
        self, load_codebase_revision, load_codebase_processes, get_codebase_languages
    ):
        codebase = Codebase(Path("."))
        codebase.setup()

        self.assertEqual(Path("Procfile").read_text(), "web: django serve")
        self.assertEqual(
            Path("buildpack-run.sh").read_text(),
            Path(__file__)
            .parent.parent.parent.parent.joinpath(
                "image_builder/codebase/load_run_environment.sh"
            )
            .read_text(),
        )

    def test_codebase_teardown(
        self, load_codebase_revision, load_codebase_processes, get_codebase_languages
    ):
        codebase = Codebase(Path("."))
        codebase.setup()
        codebase.teardown()

        self.assertEqual(
            Path("Procfile").read_text(), "web: django collectstatic && django serve"
        )
        self.assertEqual(Path("buildpack-run.sh").exists(), False)
