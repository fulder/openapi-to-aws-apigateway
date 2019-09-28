import argparse
import json

import yaml


class Generator:

    def __init__(self, openapi_path):
        self.openapi_path = openapi_path
        self.docs = None

    def generate(self):
        self._load_file()

    def _load_file(self):
        with open(self.openapi_path) as f:
            if ".json" in self.openapi_path:
                self.docs = json.load(f)
            else:
                self.docs = yaml.safe_load(f)


def main():
    args = parse_args()
    generator = Generator(args.file)

    generator.generate()


def parse_args():
    parser = argparse.ArgumentParser(description="Generate AWS ApiGateway CloudFormation from OpenAPI specification")
    parser.add_argument("--file", "-f", required=True, type=str, help="Path to the OpenAPI specification file")
    return parser.parse_args()


if __name__ == "__main__":
    main()
