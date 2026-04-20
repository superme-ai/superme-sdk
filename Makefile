.PHONY: install test test-live test-cov lint fmt typecheck check clean

install:
	uv sync --extra dev

test:
	uv run --extra dev pytest -m 'not live'

test-live:
	uv run --extra dev pytest -m live -v

test-cov:
	uv run --extra dev pytest -m 'not live' --cov=superme_sdk

lint:
	uv run --extra dev ruff check superme_sdk/ tests/

fmt:
	uv run --extra dev ruff format superme_sdk/ tests/

typecheck:
	uv run --extra dev pyright superme_sdk/

check: lint typecheck test

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
