import logging
import os
import unittest

from generator.generator import Generator, CURRENT_FOLDER, VerbExtender

logger = logging.getLogger("generator.generator")
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")


class TestGenerator(unittest.TestCase):

    def test_determine_backend_type_http(self):
        generator = Generator("test_swagger.json", "http://my-backend", False, "", "eu-west-1")
        generator._determine_backend_type()
        self.assertEqual("http", generator.backend_type)

    def test_determine_backend_type_http_proxy(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "", "eu-west-1")
        generator._determine_backend_type()
        self.assertEqual("http_proxy", generator.backend_type)

    def test_determine_backend_type_aws(self):
        generator = Generator("test_swagger.json", "arn:test:lambda:arn", False, "", "eu-west-1")
        generator._determine_backend_type()
        self.assertEqual("aws", generator.backend_type)

    def test_determine_backend_type_aws_proxy(self):
        generator = Generator("test_swagger.json", "arn:test:lambda:arn", True, "", "eu-west-1")
        generator._determine_backend_type()
        self.assertEqual("aws_proxy", generator.backend_type)

    def test_init_integration_internet_type(self):
        verb_extender = VerbExtender("get", {}, "/path1", "aws_proxy", "", True, "TEST_URI_START")
        verb_extender._init_integration()
        exp_verb = {
            "connectionType": "INTERNET",
            "httpMethod": "POST",
            "type": "aws_proxy",
            "uri": "TEST_URI_START"
        }
        self.assertEqual(exp_verb, verb_extender.integration)

    def test_init_integration_vpc_type(self):
        verb_extender = VerbExtender("get", {}, "/path1", "http_proxy", "VPC_LINK_ID", True, "TEST_URI_START")
        verb_extender._init_integration()
        exp_verb = {
            "connectionId": "VPC_LINK_ID",
            "connectionType": "VPC_LINK",
            "httpMethod": "POST",
            "type": "http_proxy",
            "uri": "TEST_URI_START"
        }
        self.assertEqual(exp_verb, verb_extender.integration)

    def test_init_integration_creates_correct_verb(self):
        verb_extender = VerbExtender("get", {}, "/path1", "http_proxy", "", False, "http://${stageVariables.httpHost}")
        verb_extender._init_integration()
        exp_verb = {
            "connectionType": "INTERNET",
            "httpMethod": "GET",
            "type": "http_proxy",
            "uri": "http://${stageVariables.httpHost}/path1"
        }
        self.assertEqual(exp_verb, verb_extender.integration)

    def test_init_integration_with_lambda_creates_post_method(self):
        verb_extender = VerbExtender("get", {}, "/path1", "aws", "", True, "TEST_START_URL")
        verb_extender._init_integration()
        exp_verb = {
            "connectionType": "INTERNET",
            "httpMethod": "POST",
            "type": "aws",
            "uri": "TEST_START_URL"
        }
        self.assertEqual(exp_verb, verb_extender.integration)

    def test_docs_version_swagger(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "", "eu-west-1")
        generator.docs = {
            "swagger": "2.0"
        }
        generator._docs_version()
        self.assertEqual("swagger", generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "swagger.yaml"), generator.output_path_openapi)

    def test_docs_version_openapi(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "", "eu-west-1")
        generator.docs = {
            "openapi": "3.0"
        }
        generator._docs_version()
        self.assertEqual("openapi", generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "openapi.yaml"), generator.output_path_openapi)

    def test_docs_version_unsupported(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "", "eu-west-1")
        generator.docs = {
            "invalid": "2.0"
        }
        self.assertRaises(RuntimeError, generator._docs_version)
