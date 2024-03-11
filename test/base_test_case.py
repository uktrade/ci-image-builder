import os

from pyfakefs.fake_filesystem_unittest import TestCase

from image_builder.const import ADDITIONAL_ECR_REPO
from image_builder.const import ECR_REPO


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.reset_environment_variables()

    @staticmethod
    def reset_environment_variables():
        os.environ.pop("CODEBUILD_BUILD_ARN", None)
        os.environ.pop(ECR_REPO, None)
        os.environ.pop(ADDITIONAL_ECR_REPO, None)
