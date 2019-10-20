.PHONY: test-coverage
test-coverage:
	PYTHONPATH=. pytest --log-level DEBUG test/ --cov=generator && coverage html

.PHONY: install-dev
install-dev:
	python3 setup.py develop --user

.PHONY: uninstall-dev
uninstall-dev:
	python3 setup.py develop --uninstall --user

.PHONY: build
build:
	python3 setup.py sdist bdist_wheel

.PHONY: publish-test
publish-test: clean build
	python3 -m pip install --user --upgrade twine
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: clean
clean:
	rm -rf dist build oai_sam.egg-info out htmlcov .pytest_cache
	rm -f .coverage