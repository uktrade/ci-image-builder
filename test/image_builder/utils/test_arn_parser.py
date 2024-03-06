import unittest
from test.image_builder.utils.exceptions import ValidationError

import pytest
from parameterized import parameterized

from image_builder.configuration.codebase import CodebaseConfigurationLoadError
from image_builder.utils.arn_parser import ARN


class TestArnParser(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.source_arn = (
            "arn:partition:service:region:account-id:resource-type:resource-id"
        )

    def test_arn_parser_properties(self):
        arn = ARN(self.source_arn)

        self.assertEqual(arn.source, self.source_arn)
        self.assertEqual(arn.partition, "partition")
        self.assertEqual(arn.service, "service")
        self.assertEqual(arn.region, "region")
        self.assertEqual(arn.account_id, "account-id")
        self.assertEqual(arn.project, "resource-type")
        self.assertEqual(arn.build_id, "resource-id")

    @parameterized.expand(
        [
            "",
            "arn:partition:service:region:account-id",
        ]
    )
    def test_arn_parser_raises_error_if_arn_not_valid(self, arn):
        with pytest.raises(ValidationError, match=f"Invalid ARN: {arn}"):
            ARN(arn)
