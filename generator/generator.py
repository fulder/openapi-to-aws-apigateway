import argparse
import copy
import json
import logging
import os
import re
import shutil
from urllib.parse import urlparse

import yaml

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, openapi_path: str, backend_url: str, proxy: bool, vpc_link_id: str, apigateway_region: str):
        self.openapi_path = openapi_path
        self.backend_url = backend_url
        self.proxy = proxy
        self.vpc_link_id = vpc_link_id
        self.apigateway_region = apigateway_region

        self.output_folder = os.path.abspath(os.path.join(CURRENT_FOLDER, "out"))
        self.output_path_sam = os.path.join(self.output_folder, "apigateway.yaml")
        self.stage_variables = {"backendUrl": self.backend_url}

        # Created by helper funcs during generate
        self.docs = None
        self.backend_type = None
        self.backend_uri_start = None
        self.docs_type = None
        self.output_path_openapi = None
        self.cloudformation = None

    def generate(self):
        # Don't dump reference pointers
        yaml.SafeDumper.ignore_aliases = lambda *args: True

        self._create_empty_output_folder()
        self._load_file()
        self._docs_version()

        self._determine_backend_type()
        self._create_backend_uri_start()

        self._init_sam_template()

        self._extend_verbs()

        self._save_openapi()
        self._save_cloudformation()

    def _create_empty_output_folder(self):
        if os.path.isdir(self.output_folder):
            shutil.rmtree(self.output_folder)
        os.mkdir(self.output_folder)

    @property
    def is_lambda_integration(self):
        return self.backend_url.startswith("arn:")

    def _load_file(self):
        with open(self.openapi_path, "r") as f:
            if ".json" in self.openapi_path:
                self.docs = json.load(f)
            else:
                self.docs = yaml.safe_load(f)

    def _docs_version(self):
        if "swagger" in self.docs and self.docs["swagger"].startswith("2.0"):
            self.docs_type = "swagger"
            self.output_path_openapi = os.path.join(self.output_folder, "swagger.yaml")
        elif "openapi" in self.docs and self.docs["openapi"].startswith("3.0"):
            self.docs_type = "openapi"
            self.output_path_openapi = os.path.join(self.output_folder, "openapi.yaml")
        else:
            raise RuntimeError("Unsupported docs type. Supported: Swagger 2.0, OpenAPI 3.0")

    def _init_sam_template(self):
        self.cloudformation = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Transform": "AWS::Serverless-2016-10-31",
            "Description": "ApiGateway stack auto generated by openapi-aws-apigateway-generator",
            "Resources": {
                "Api": {
                    "Type": "AWS::Serverless::Api",
                    "Properties": {
                        "StageName": "default",
                        "DefinitionUri": self.output_path_openapi,
                        "Variables": self.stage_variables,
                    }
                }
            }
        }

    def _determine_backend_type(self):
        if self.is_lambda_integration:
            self.backend_type = "aws"
        else:
            self.backend_type = "http"

        if self.proxy:
            self.backend_type += "_proxy"
        logger.debug("Determined backend type as: [%s]", self.backend_type)

    def _create_backend_uri_start(self):
        if self.is_lambda_integration:
            m1 = re.search(r"(arn:aws:lambda::\d+:function:\w+):(\w+)", self.backend_url)
            m2 = re.search(r"(arn:aws:lambda::\d+:function:)(\w+)", self.backend_url)

            self.backend_uri_start = "arn:aws:apigateway:{}:lambda:path/2015-03-31/functions/".format(self.apigateway_region)

            if m1:
                logger.info("Setting 'lambdaVersion' stageVariable to: [%s]", m1.group(2))
                self.backend_uri_start += m1.group(1) + "${stageVariables.lambdaVersion}" + "/invocations"
                self.stage_variables["lambdaVersion"] = m1.group(2)
            elif m2:
                logger.info("Setting 'lambdaName' stageVariable to [%s]", m2.group(2))
                self.backend_uri_start += m2.group(1) + "${stageVariables.lambdaName}" + "/invocations"
                self.stage_variables["lambdaName"] = m2.group(2)
            else:
                raise RuntimeError("Invalid lambda ARN")
        else:
            parsed_url = urlparse(self.backend_url)
            logger.info("Setting 'httpHost' stageVariable to [%s]", parsed_url.hostname)
            self.backend_uri_start = "http://" + "${stageVariables.httpHost}"
            self.stage_variables["httpHost"] = parsed_url.hostname

    def _extend_verbs(self):
        extended_docs = copy.deepcopy(self.docs)

        for p in self.docs["paths"]:
            for v in self.docs["paths"][p]:
                verb = self.docs["paths"][p][v]

                logger.debug("Extending verb for route [%s %s]", v, p)
                verb_extender = VerbExtender(v, verb, p, self.backend_type, self.vpc_link_id,
                                             self.is_lambda_integration, self.backend_uri_start)
                extended_docs["paths"][p][v] = verb_extender.extend()

        self.docs = extended_docs

    def _save_openapi(self):
        with open(self.output_path_openapi, "w") as f:
            yaml.safe_dump(self.docs, f, default_flow_style=False, sort_keys=False)
        logger.info("Saved OpenAPI template with amazon extensions to: [%s]", self.output_path_openapi)

    def _save_cloudformation(self):
        with open(self.output_path_sam, "w") as f:
            yaml.safe_dump(self.cloudformation, f, default_flow_style=False, sort_keys=False)
        logger.info("Saved SAM template file to: [%s]", self.output_path_sam)


class VerbExtender:

    def __init__(self, verb: str, verb_docs: dict, path: str, backend_type: str, vpc_link_id: str,
                 is_lambda_integration: bool, backend_url_start: str):
        self.verb = verb
        self.verb_docs = verb_docs
        self.path = path
        self.vpc_link_id = vpc_link_id
        self.is_lambda_integration = is_lambda_integration
        self.integration = {
            "type": backend_type
        }
        self.backend_url_start = backend_url_start

    def extend(self) -> dict:
        self._init_integration()
        self._create_integration()

        return self.verb_docs

    def _init_integration(self):
        if self.vpc_link_id:
            logger.debug("Adding connectionId: [%s] to integrations", self.vpc_link_id)
            self.integration["connectionId"] = self.vpc_link_id
            self.integration["connectionType"] = "VPC_LINK"
        else:
            self.integration["connectionType"] = "INTERNET"

        if self.is_lambda_integration:
            self.integration["httpMethod"] = "POST"
            self.integration["uri"] = self.backend_url_start
        else:
            self.integration["httpMethod"] = self.verb.upper()
            self.integration["uri"] = self.backend_url_start + self.path

    def _create_integration(self):
        self._add_requests()
        self._add_responses()

        self.verb_docs["x-amazon-apigateway-integration"] = self.integration

    def _add_requests(self):
        params = self.verb_docs.get("parameters")
        if params:
            self.integration["requestParameters"] = {}

            for p in params:
                integration_name = p.get("in")
                param_name = p.get("name")

                if integration_name not in ["query", "path", "header"]:
                    logger.debug("Skipping verb parameter with integration name: [%s]", integration_name)
                    continue

                if integration_name == "query":
                    # special case for query name, different in requestParameters compared to openapi spec
                    integration_name = "querystring"

                mapping_name = "integration.requests.{}.{}".format(integration_name, param_name)
                mapping_value = "method.request.{}.{}".format(integration_name, param_name)
                logger.info("Mapping: [%s] to [%s] in requestParameters", mapping_name, mapping_value)
                self.integration["requestParameters"][mapping_name] = mapping_value

    def _add_responses(self):
        responses = self.verb_docs.get("responses")
        if responses:
            self.integration["responses"] = {}
            logger.debug("Adding responses for verb")

            amz_responses = {}
            for r in responses:
                amz_responses[r] = {
                    "statusCode": r,
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }
            self.integration["responses"] = amz_responses


def main():
    parser = argparse.ArgumentParser(description="Generate AWS ApiGateway CloudFormation from OpenAPI specification")
    # Required params
    parser.add_argument("--file", "-f", required=True, type=str, help="Path to the OpenAPI specification file")
    parser.add_argument("--backend_url", "-u", required=True, type=str,
                        help="Backend URL to forward the requests to (use ARN for lambda backend)")

    # Optional params
    parser.add_argument("--apigateway_region", "-r", required=False,
                        help="Region where ApiGateway will be deployed. Only needed for lambda integration")
    parser.add_argument("--proxy", "-p", required=False, action="store_true", help="Proxy all requests to the backend")
    parser.add_argument("--vpc_link_id", "-v", required=False, help="If backend is an VPC link, provide the link ID")
    args = parser.parse_args()
    generator = Generator(args.file, args.backend_url, args.proxy, args.vpc_link_id, args.apigateway_region)
    generator.generate()


if __name__ == "__main__":
    logger.addHandler(logging.StreamHandler())
    logger.setLevel("DEBUG")
    main()
