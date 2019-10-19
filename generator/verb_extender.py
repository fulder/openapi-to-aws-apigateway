import logging

logger = logging.getLogger(__name__)


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

                mapping_name = "integration.request.{}.{}".format(integration_name, param_name)
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

        for r in responses:
            if "headers" not in self.verb_docs["responses"][r]:
                self.verb_docs["responses"][r]["headers"] = {}

            self.verb_docs["responses"][r]["headers"]["Access-Control-Allow-Origin"] = {
                "type": "string",
                "description": "CORS origin header added by openapi-aws-apigateway-generator"
            }
