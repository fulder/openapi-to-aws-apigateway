.PHONY: test-coverage
test-coverage:
	PYTHONPATH=. pytest --log-level DEBUG test/ --cov=generator && coverage html