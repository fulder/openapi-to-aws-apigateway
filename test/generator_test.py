import json
import logging
import os
import shutil
import unittest

from generator.generator import Generator, CURRENT_FOLDER, VerbExtender

logger = logging.getLogger("generator.generator")
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")


class TestGenerator(unittest.TestCase):

    def setUp(self) -> None:
        self.current_folder = os.path.dirname(os.path.realpath(__file__))
        self.input_file = os.path.join(self.current_folder, "petshop.json")
        self.generator = Generator(self.input_file, "http://petstore.execute-api.eu-west-1.amazonaws.com/petstore", False, "", "eu-west-1")

    def test_generate_petshop(self):
        self.generator.generate()
        with open(os.path.join(self.current_folder, "petshop_extended.json")) as f:
            exp = json.load(f)
        self.maxDiff = None
        self.assertEqual(exp, self.generator.docs)

    def test_determine_backend_type_http(self):
        self.generator._determine_backend_type()
        self.assertEqual("http", self.generator.backend_type)

    def test_determine_backend_type_http_proxy(self):
        self.generator.proxy = True
        self.generator._determine_backend_type()
        self.assertEqual("http_proxy", self.generator.backend_type)

    def test_determine_backend_type_aws(self):
        self.generator.backend_url = "arn:test:lambda:arn"
        self.generator._determine_backend_type()
        self.assertEqual("aws", self.generator.backend_type)

    def test_determine_backend_type_aws_proxy(self):
        self.generator.backend_url = "arn:test:lambda:arn"
        self.generator.proxy = True
        self.generator._determine_backend_type()
        self.assertEqual("aws_proxy", self.generator.backend_type)

    def test_docs_version_swagger(self):
        self.generator.docs = {
            "swagger": "2.0"
        }
        self.generator._docs_version()
        self.assertEqual("swagger", self.generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "swagger.yaml"), self.generator.output_path_openapi)

    def test_docs_version_openapi(self):
        self.generator.docs = {
            "openapi": "3.0"
        }
        self.generator._docs_version()
        self.assertEqual("openapi", self.generator.docs_type)
        self.assertEqual(os.path.join(CURRENT_FOLDER, "out", "openapi.yaml"), self.generator.output_path_openapi)

    def test_docs_version_unsupported(self):
        self.generator.docs = {
            "invalid": "2.0"
        }
        self.assertRaises(RuntimeError, self.generator._docs_version)

    def test_create_backend_uri_start_lambda_with_version(self):
        self.generator.backend_url = "arn:aws:lambda::123123:function:TEST_NAME:TEST_VERSION"
        self.generator.apigateway_region = "eu-west-1"
        self.generator._create_backend_uri_start()
        exp = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda::123123:function:TEST_NAME:${stageVariables.lambdaVersion}/invocations"
        self.assertEqual(exp, self.generator.backend_uri_start)
        self.assertIn("lambdaVersion", self.generator.stage_variables)
        self.assertEqual("TEST_VERSION", self.generator.stage_variables["lambdaVersion"])

    def test_create_backend_uri_start_lambda_name(self):
        self.generator.backend_url = "arn:aws:lambda::123123:function:TEST_NAME"
        self.generator.apigateway_region = "eu-west-1"
        self.generator._create_backend_uri_start()
        exp = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda::123123:function:${stageVariables.lambdaName}/invocations"
        self.assertEqual(exp, self.generator.backend_uri_start)
        self.assertIn("lambdaName", self.generator.stage_variables)
        self.assertEqual("TEST_NAME", self.generator.stage_variables["lambdaName"])

    def test_create_backend_uri_invalid_arn_raises_runtime(self):
        self.generator.backend_url = "arn:aws:lam:INVALID"
        self.generator.apigateway_region = "eu-west-1"
        self.assertRaises(RuntimeError, self.generator._create_backend_uri_start)

    def test_create_backend_uri_start_http(self):
        self.generator.backend_url = "http://my-backend.com"
        self.generator._create_backend_uri_start()
        exp = "http://${stageVariables.httpHost}"
        self.assertEqual(exp, self.generator.backend_uri_start)
        self.assertIn("httpHost", self.generator.stage_variables)
        self.assertEqual("my-backend.com", self.generator.stage_variables["httpHost"])

    def tearDown(self) -> None:
        if os.path.isdir(self.generator.output_folder):
            shutil.rmtree(self.generator.output_folder)
