[![Build Status](https://travis-ci.com/fulder/openapi-to-aws-apigateway.svg?branch=master)](https://travis-ci.com/fulder/openapi-to-aws-apigateway)
[![Coverage Status](https://coveralls.io/repos/github/fulder/openapi-to-aws-apigateway/badge.svg?branch=master)](https://coveralls.io/github/fulder/openapi-to-aws-apigateway?branch=master)
[![Python Version](https://img.shields.io/badge/python-2.7%2C3.3%2B-blue.svg)](https://www.python.org/)

`oai-sam-api` is a script generating a SAM template together with OpenAPI documentation including [AWS OpenAPI extensions](https://docs.aws.amazon.com/en_pv/apigateway/latest/developerguide/api-gateway-swagger-extensions.html) from an OpenAPI/swagger documentation.

Simply provide your OpenApi/Swagger as an input and then use [SAM CLI](https://docs.aws.amazon.com/en_pv/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) to deploy a working AWS ApiGateway.  

# Install

`pip install oai-sam-api`

# Usage

## Generate
`oai-sam-api -f <OPENAPI_DOCS> -u <BACKEND_URL> -c <CORS_ORIGINS>`

e.g:

`oai-sam-api -f https://petstore.swagger.io/v2/swagger.json -u http://petstore.swagger.io/v2 -c "*"`

## Deploy AWS ApiGateway

* Install [SAM CLI](https://docs.aws.amazon.com/en_pv/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* `sam package --template-file out/apigateway.yaml --s3-bucket <SAM_BUCKET> --output-file packaged.yaml` (See [sam package](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-package.html) for more options)
* `sam deploy --template-file packaged.yaml`

## Show list of available arguments
`oai-sam-api --help`