.PHONY: test-coverage
test-coverage:
	PYTHONPATH=. pytest --log-level DEBUG test/generator_test.py --cov=generator.generator && coverage html