import argparse
import json
import logging
import os

import yaml

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, openapi_path: str, backend_url: str, proxy: bool):
        self.openapi_path = openapi_path
        self.backend_url = backend_url
        self.proxy = proxy
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

        self._add_responses()

        self._save_cloudformation()

    def _load_file(self):
        with open(self.openapi_path, "r") as f:
            if ".json" in self.openapi_path:
                self.docs = json.load(f)
            else:
                self.docs = yaml.safe_load(f)

    def _determine_type(self):
        if self.backend_url.startswith("arn:"):
            self.type = "aws"
        else:
            self.type = "http"

        if self.proxy:
            self.type += "_proxy"

    def _add_responses(self):
        for p in self.docs["paths"]:
            for v in self.docs["paths"][p]:
                verb = self.docs["paths"][p][v]
                responses = verb.get("responses")
                if not responses:
                    logger.debug("[%s %s] has no responses")
                    continue

                amz_responses = {}
                for r in responses:
                    amz_responses[r] = {
                        "statusCode": r,
                    }

                verb["x-amazon-apigateway-integration"] = {"responses": amz_responses}

    def _save_cloudformation(self):
        with open(self.cloudformation_path, "w") as f:
            yaml.safe_dump(self.cloudformation, f, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(description="Generate AWS ApiGateway CloudFormation from OpenAPI specification")
    parser.add_argument("--file", "-f", required=True, type=str, help="Path to the OpenAPI specification file")
    parser.add_argument("--backend_url", "-u", required=True, type=str,
                        help="Backend URL to forward the requests to (use ARN for lambda backend)")
    parser.add_argument("--proxy", "-p", action="store_true", help="Proxy all requests to the backend")
    args = parser.parse_args()
    generator = Generator(args.file, args.backend_url, args.proxy)
    generator.generate()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel("DEBUG")
    main()
