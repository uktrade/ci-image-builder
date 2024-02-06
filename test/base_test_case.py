import os

from pyfakefs.fake_filesystem_unittest import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.reset_environment_variables()

    def reset_environment_variables(self):
        os.environ.pop("CODEBUILD_BUILD_ARN", None)
        os.environ.pop("ECR_REPOSITORY", None)
