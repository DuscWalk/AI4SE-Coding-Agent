.PHONY: test test-demo test-all lint typecheck clean

test:
	pytest tests/ -v --tb=short --ignore=tests/demonstrations

test-demo:
	pytest tests/demonstrations/ -v --tb=short

test-all:
	pytest tests/ -v --tb=short

lint:
	ruff check coding_agent/

typecheck:
	mypy coding_agent/ --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true