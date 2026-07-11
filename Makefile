.PHONY: test test-demo test-all lint typecheck check clean

test:
	pytest tests/ -v --tb=short --ignore=tests/demonstrations

test-demo:
	pytest tests/demonstrations/ -v --tb=short

test-all:
	pytest tests/ -v --tb=short

lint:
	ruff check coding_agent/ tests/

typecheck:
	mypy coding_agent/ --strict --ignore-missing-imports

check: lint typecheck test-all

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
