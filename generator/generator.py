import argparse
import json
import logging
import os

import yaml

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, openapi_path: str, backend_url: str, proxy: bool, vpc_link_id: str):
        self.openapi_path = openapi_path
        self.backend_url = backend_url
        self.proxy = proxy
        self.vpc_link_id = vpc_link_id
        self.cloudformation_path = os.path.abspath(os.path.join(CURRENT_FOLDER, "apigateway.yaml"))
        self.cloudformation = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "RestApi": {
                    "Type": "AWS::ApiGateway::RestApi"
                }
            }
        }

        # Created by helper funcs during generate
        self.docs = None
        self.type = None

    def generate(self):
        self._load_file()
        self._determine_type()

        self._extend_verbs()

        self._save_cloudformation()

    @property
    def is_lambda_integration(self):
        return self.backend_url.startswith("arn:")

    def _load_file(self):
        with open(self.openapi_path, "r") as f:
            if ".json" in self.openapi_path:
                self.docs = json.load(f)
            else:
                self.docs = yaml.safe_load(f)

    def _determine_type(self):
        if self.is_lambda_integration:
            self.type = "aws"
        else:
            self.type = "http"

        if self.proxy:
            self.type += "_proxy"

    def _extend_verbs(self):
        integration = self._init_integration()

        for p in self.docs["paths"]:
            for v in self.docs["paths"][p]:
                verb = self.docs["paths"][p][v]

                logger.debug("Adding integration to [%s %s]", v, p)
                self._create_integration(v, verb, integration)

    def _init_integration(self) -> dict:
        integration = {
            "responses": {}
        }
        if self.vpc_link_id:
            logger.debug("Adding connectionId: [%s] to all integrations", self.vpc_link_id)
            integration["connectionId"] = self.vpc_link_id
            integration["connectionType"] = "VPC_LINK"
        else:
            integration["connectionType"] = "INTERNET"
        return integration

    def _create_integration(self, method: str, verb: dict, integration: dict):
        if self.is_lambda_integration:
            integration["httpMethod"] = "POST"
        else:
            integration["httpMethod"] = method

        responses = verb.get("responses")
        if responses:
            logger.debug("Adding responses for verb")

            amz_responses = verb["x-amazon-apigateway-integration"]
            for r in responses:
                amz_responses[r] = {
                    "statusCode": r,
                    "type": self.type
                }
            integration["responses"] = amz_responses

        verb["x-amazon-apigateway-integration"] = integration

    def _save_cloudformation(self):
        with open(self.cloudformation_path, "w") as f:
            yaml.safe_dump(self.cloudformation, f, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(description="Generate AWS ApiGateway CloudFormation from OpenAPI specification")
    # Required params
    parser.add_argument("--file", "-f", required=True, type=str, help="Path to the OpenAPI specification file")
    parser.add_argument("--backend_url", "-u", required=True, type=str,
                        help="Backend URL to forward the requests to (use ARN for lambda backend)")

    # Optional params
    parser.add_argument("--proxy", "-p", required=False, action="store_true", help="Proxy all requests to the backend")
    parser.add_argument("--vpc_link_id", "-v", required=False, help="If backend is an VPC link, provide the link ID")
    args = parser.parse_args()
    generator = Generator(args.file, args.backend_url, args.proxy, args.vpc_link_id)
    generator.generate()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel("DEBUG")
    main()
