import argparse
import json
import logging
import os

import yaml

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, openapi_path):
        self.openapi_path = openapi_path
        self.docs = None
        self.cloudformation_path = os.path.abspath(os.path.join(CURRENT_FOLDER, "apigateway.yaml"))
        self.cloudformation = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "RestApi": {
                    "Type": "AWS::ApiGateway::RestApi"
                }
            }
        }

    def generate(self):
        self._load_file()

        self._save_cloudformation()

    def _load_file(self):
        with open(self.openapi_path, "r") as f:
            if ".json" in self.openapi_path:
                self.docs = json.load(f)
            else:
                self.docs = yaml.safe_load(f)

    def _save_cloudformation(self):
        with open(self.cloudformation_path, "w") as f:
            yaml.safe_dump(self.cloudformation, f, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(description="Generate AWS ApiGateway CloudFormation from OpenAPI specification")
    parser.add_argument("--file", "-f", required=True, type=str, help="Path to the OpenAPI specification file")
    args = parser.parse_args()
    generator = Generator(args.file)
    generator.generate()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel("DEBUG")
    main()
