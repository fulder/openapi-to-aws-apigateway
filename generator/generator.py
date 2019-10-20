import copy
import json
import logging
import os
import re
import shutil

try:
    from urllib.parse import urlparse
except ImportError:
    # Python2 only
    from urlparse import urlparse

import yaml

from .verb_extender import VerbExtender

CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CORS_MAPPING_TEMPLATE_OPTIONS = """
#if ($input.params("Origin") !="" && $stageVariables.CORS_ORIGINS != "" && $input.params("Origin") in $stageVariables.CORS_ORIGINS.split(","))
    #$context.responseOverride.header.Access-Control-Allow-Origin=$input.params("Origin")
    #$context.responseOverride.header.Access-Control-Allow-Headers={headers}
    #$context.responseOverride.header.Access-Control-Allow-Methods={methods}
#end
""".replace("\n", "")

logger = logging.getLogger(__name__)


class Generator:

    def __init__(self, openapi_path, backend_url, proxy, vpc_link_id, apigateway_region):
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
        self._enable_cors()

        self._remove_unsupported_model_properties()

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
            m1 = re.search(r"(arn:aws:lambda::\d+:function:\w+:)(\w+)", self.backend_url)
            m2 = re.search(r"(arn:aws:lambda::\d+:function:)(\w+)", self.backend_url)

            self.backend_uri_start = "arn:aws:apigateway:{}:lambda:path/2015-03-31/functions/".format(
                self.apigateway_region)

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

    def _enable_cors(self):
        extended_docs = copy.deepcopy(self.docs)

        for p in self.docs["paths"]:
            extended_docs["paths"][p]["options"] = {
                "summary": "CORS support",
                "description": "Enable CORS by returning correct headers",
                "consumes": [
                    "application/json"
                ],
                "produces": [
                    "application/json"
                ],
                "tags": [
                    "CORS"
                ],
                "x-amazon-apigateway-integration": {
                    "type": "mock",
                    "responses": {
                        "default": {
                            "statusCode": "200",
                            "responseTemplates": {
                                "application/json": CORS_MAPPING_TEMPLATE_OPTIONS
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Default response for CORS method",
                        "headers": {
                            "Access-Control-Allow-Headers": {
                                "type": "string"
                            },
                            "Access-Control-Allow-Methods": {
                                "type": "string"
                            },
                            "Access-Control-Allow-Origin": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
            self.docs = extended_docs

    def _remove_unsupported_model_properties(self):
        """
        Removing unsupported properties see:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-known-issues.html#api-gateway-known-issues-rest-apis
        :return:
        """
        if "definitions" not in self.docs:
            logger.debug("No definitions in docs")
            return

        extended_docs = copy.deepcopy(self.docs)

        for d in self.docs["definitions"]:
            def_docs = extended_docs["definitions"][d]
            if def_docs.get("xml"):
                logger.info("Removing unsupported xml in definition [%s]", d)
                del def_docs["xml"]

            properties = def_docs.get("properties")
            if not properties:
                logger.debug("No properties in definition: [%s]", d)
                continue

            for prop in properties:
                if properties[prop].get("xml"):
                    logger.info("Removing unsupported xml in definition [%s] property [%s]", d, prop)
                    del properties[prop]["xml"]

                if properties[prop].get("example"):
                    logger.info("Removing unsupported example in definition [%s] property [%s]", d, prop)
                    del properties[prop]["example"]

        self.docs = extended_docs

    def _save_openapi(self):
        with open(self.output_path_openapi, "w") as f:
            yaml.safe_dump(self.docs, f, default_flow_style=False, sort_keys=False)
        logger.info("Saved OpenAPI template with amazon extensions to: [%s]", self.output_path_openapi)

    def _save_cloudformation(self):
        with open(self.output_path_sam, "w") as f:
            yaml.safe_dump(self.cloudformation, f, default_flow_style=False, sort_keys=False)
        logger.info("Saved SAM template file to: [%s]", self.output_path_sam)
