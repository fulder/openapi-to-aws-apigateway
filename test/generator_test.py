import logging
import unittest

from generator.generator import Generator

logger = logging.getLogger("generator.generator")
logger.setLevel("DEBUG")


class TestGenerator(unittest.TestCase):

    def setUp(self) -> None:
        self.generator = Generator("test_swagger.json", "http://my-backend", False, "")

    def test_determine_type_http(self):
        generator = Generator("test_swagger.json", "http://my-backend", False, "")
        generator._determine_type()
        self.assertEqual("http", generator.backend_type)

    def test_determine_type_http_proxy(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator._determine_type()
        self.assertEqual("http_proxy", generator.backend_type)

    def test_determine_type_aws(self):
        generator = Generator("test_swagger.json", "arn:test:lambda:arn", False, "")
        generator._determine_type()
        self.assertEqual("aws", generator.backend_type)

    def test_determine_type_aws_proxy(self):
        generator = Generator("test_swagger.json", "arn:test:lambda:arn", True, "")
        generator._determine_type()
        self.assertEqual("aws_proxy", generator.backend_type)


