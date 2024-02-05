import os


class BaseTestCase(BaseTestCase):
    def setUp(self):
        os.environ.pop("CODEBUILD_BUILD_ARN", None)
        os.environ.pop("ECR_REPOSITORY", None)
