.PHONY: test-coverage
test-coverage:
	PYTHONPATH=. pytest --log-level DEBUG test/ --cov=generator.generator --cov=generator.verb_extender && coverage html