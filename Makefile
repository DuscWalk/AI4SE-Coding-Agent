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
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"