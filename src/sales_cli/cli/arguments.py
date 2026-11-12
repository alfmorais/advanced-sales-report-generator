"""Command-line argument definition, parsing and validation."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from sales_cli.core.rules import validate_period
from sales_cli.errors import InvalidPeriodError

DEFAULT_OUTPUT_FORMATS: Final[tuple[str, ...]] = ("text", "json")
LOG_LEVELS: Final[tuple[str, ...]] = ("DEBUG", "INFO", "WARNING", "ERROR")
DATE_FORMAT: Final = "YYYY-MM-DD"


@dataclass(frozen=True, slots=True)
class Arguments:
    """Validated command-line arguments."""

    path: Path
    output_format: str
    start: date | None
    end: date | None
    log_level: str


def parse_date(value: str) -> date:
    """Convert a YYYY-MM-DD string into a ``date``."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date '{value}'; use the format {DATE_FORMAT}"
        ) from exc


def create_parser(
    output_formats: Sequence[str] = DEFAULT_OUTPUT_FORMATS,
) -> argparse.ArgumentParser:
    """Build the parser; output formats come from the renderers."""
    parser = argparse.ArgumentParser(
        prog="sales-cli",
        description=(
            "Generate a sales report (totals per product, grand total and "
            "top-selling product) from a CSV file."
        ),
        epilog=(
            "Required CSV columns: data (YYYY-MM-DD), produto, quantidade, "
            "valor_unitario. Example: sales-cli sales.csv --format json "
            "--start 2025-01-01 --end 2025-03-31"
        ),
    )
    parser.add_argument("csv", type=Path, help="path to the sales CSV file")
    parser.add_argument(
        "--format",
        choices=tuple(output_formats),
        default=output_formats[0],
        help=f"output format (default: {output_formats[0]})",
    )
    parser.add_argument(
        "--start",
        type=parse_date,
        metavar=DATE_FORMAT,
        help="start date of the filter, inclusive",
    )
    parser.add_argument(
        "--end",
        type=parse_date,
        metavar=DATE_FORMAT,
        help="end date of the filter, inclusive",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="WARNING",
        help="log level written to stderr (default: WARNING)",
    )
    return parser


def parse_arguments(
    argv: Sequence[str] | None = None,
    output_formats: Sequence[str] = DEFAULT_OUTPUT_FORMATS,
) -> Arguments:
    """Parse and validate the arguments. Usage errors exit with code 2."""
    parser = create_parser(output_formats)
    namespace = parser.parse_args(argv)

    try:
        validate_period(namespace.start, namespace.end)
    except InvalidPeriodError as exc:
        parser.error(str(exc))

    return Arguments(
        path=namespace.csv,
        output_format=namespace.format,
        start=namespace.start,
        end=namespace.end,
        log_level=namespace.log_level,
    )
