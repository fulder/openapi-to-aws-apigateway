import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="oai-sam-api",
    version="0.0.2",
    author="Michal Sadowski",
    entry_points={
        "console_scripts": [
            "oai-sam-api = generator.__main__:main",
        ]
    },
    author_email="misad90@gmail.com",
    description="Generate SAM template and AWS OpenAPI extended docs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fulder/openapi-to-aws-apigateway",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.6, >=3.3',
)