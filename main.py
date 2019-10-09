import argparse
import logging

from generator.generator import Generator


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
    logger = logging.getLogger("generator")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel("DEBUG")
    main()
