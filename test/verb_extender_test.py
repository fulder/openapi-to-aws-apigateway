import logging
import os
import unittest

from generator.generator import VerbExtender

logger = logging.getLogger("generator.verb_extender")
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")


class TestVerbExtender(unittest.TestCase):

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
