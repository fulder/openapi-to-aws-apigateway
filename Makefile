.PHONY: test-coverage
test-coverage:
	PYTHONPATH=. pytest --log-level DEBUG test/ --cov=generator && coverage html

.PHONY: install-dev
install-dev:
	python3 setup.py develop --user

.PHONY: uninstall-dev
uninstall-dev:
	python3 setup.py develop --uninstall --user