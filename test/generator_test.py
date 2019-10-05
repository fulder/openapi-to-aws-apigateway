import logging
import os
import unittest

from generator.generator import Generator, CURRENT_FOLDER

logger = logging.getLogger("generator.generator")
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")


class TestGenerator(unittest.TestCase):

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

    def test_init_integration_internet_type(self):
        generator = Generator("test_swagger.json", "arn:test:lambda:arn", True, "")
        generator._determine_type()
        integration = generator._init_integration()
        exp_integration = {
            "responses": {},
            "connectionType": "INTERNET",
            "type": "aws_proxy",
            "requestParameters": {}
        }
        self.assertEqual(exp_integration, integration)

    def test_init_integration_vpc_type(self):
        generator = Generator("test_swagger.json", "http://vpc_endpoint", True, "VPC_LINK_ID")
        generator._determine_type()
        integration = generator._init_integration()
        exp_integration = {
            "responses": {},
            "connectionId": "VPC_LINK_ID",
            "connectionType": "VPC_LINK",
            "type": "http_proxy",
            "requestParameters": {},
        }
        self.assertEqual(exp_integration, integration)

    def test_create_integration_creates_correct_verb(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator._determine_type()
        integration = generator._init_integration()
        verb = {}
        generator._create_integration("TEST_VERB", "/path1", verb, integration)
        exp_verb = {
            "x-amazon-apigateway-integration": {
                "connectionType": "INTERNET",
                "httpMethod": "TEST_VERB",
                "responses": {},
                'requestParameters': {},
                "type": "http_proxy",
                "uri": "http://my-backend/path1"
            }
        }
        self.assertEqual(exp_verb, verb)

    def test_create_integration_with_lambda_creates_post_method(self):
        generator = Generator("test_swagger.json", "arn:lambda", True, "")
        generator._determine_type()
        integration = generator._init_integration()
        verb = {}
        generator._create_integration("TEST_VERB", "/path1", verb, integration)
        exp_verb = {
            "x-amazon-apigateway-integration": {
                "connectionType": "INTERNET",
                "httpMethod": "POST",
                "responses": {},
                "requestParameters": {},
                "type": "aws_proxy",
                "uri": "arn:lambda"
            }
        }
        self.assertEqual(exp_verb, verb)

    def test_create_integration_with_responses(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator._determine_type()
        integration = generator._init_integration()
        verb = {
            "responses": {
                "200": {},
                "400": {}
            }
        }
        generator._create_integration("TEST_VERB", "/path1", verb, integration)
        exp_verb = {
            "responses": {
                "200": {},
                "400": {}
            },
            "x-amazon-apigateway-integration": {
                "connectionType": "INTERNET",
                "httpMethod": "TEST_VERB",
                "responses": {
                    "200": {
                        "statusCode": "200"
                    },
                    "400": {
                        "statusCode": "400"
                    }
                },
                "requestParameters": {},
                "type": "http_proxy",
                "uri": "http://my-backend/path1"
            }
        }
        self.assertEqual(exp_verb, verb)

    def test_docs_version_swagger(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator.docs = {
            "swagger": "2.0"
        }
        generator._docs_version()
        self.assertEqual("swagger", generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "swagger.yaml"), generator.output_path_openapi)

    def test_docs_version_openapi(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator.docs = {
            "openapi": "3.0"
        }
        generator._docs_version()
        self.assertEqual("openapi", generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "openapi.yaml"), generator.output_path_openapi)

    def test_docs_version_unsupported(self):
        generator = Generator("test_swagger.json", "http://my-backend", True, "")
        generator.docs = {
            "invalid": "2.0"
        }
        self.assertRaises(RuntimeError, generator._docs_version)