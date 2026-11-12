check:
	@uv run ruff check . --fix

format:
	@uv run ruff format .

mypy-check:
	@uv run mypy

unit-tests:
	@uv run pytest -vvv --cov=src --cov-report=term-missing