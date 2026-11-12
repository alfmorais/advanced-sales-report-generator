"""Composition root: wires the concrete implementations and runs the CLI."""

from collections.abc import Mapping, Sequence
from typing import Final

from sales_cli.cli.app import run
from sales_cli.cli.output import Renderer, format_json, format_text
from sales_cli.core.service import ReportService
from sales_cli.parsers.csv_reader import CsvSalesReader

RENDERERS: Final[Mapping[str, Renderer]] = {
    "text": format_text,
    "json": format_json,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Build the dependency graph and run the CLI."""
    service = ReportService(CsvSalesReader())
    return run(argv, service=service, renderers=RENDERERS)


if __name__ == "__main__":
    raise SystemExit(main())
