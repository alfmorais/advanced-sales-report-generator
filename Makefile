check:
	@uv run ruff check . --fix

format:
	@uv run ruff format .

mypy-check:
	@mypy --config-file=pyproject.toml .

unit-tests:
	@uv run pytest -vvv --cov=src --cov-report=term-missing