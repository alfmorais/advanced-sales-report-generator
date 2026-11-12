"""CSV adapter: validates the input path and reads sales from CSV files."""

import csv
import logging
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, TextIO

from sales_cli.core.models import Sale
from sales_cli.errors import (
    InputFileNotFoundError,
    InvalidCsvError,
    SalesError,
)

logger = logging.getLogger(__name__)

COLUMN_DATE: Final = "data"
COLUMN_PRODUCT: Final = "produto"
COLUMN_QUANTITY: Final = "quantidade"
COLUMN_UNIT_PRICE: Final = "valor_unitario"
REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    COLUMN_DATE,
    COLUMN_PRODUCT,
    COLUMN_QUANTITY,
    COLUMN_UNIT_PRICE,
)
CSV_ENCODING: Final = "utf-8-sig"
DATE_FORMAT: Final = "YYYY-MM-DD"


def validate_path(path: Path) -> None:
    """Check that the path points to an existing file."""
    if not path.exists():
        raise InputFileNotFoundError(f"file not found: '{path}'")
    if not path.is_file():
        raise InputFileNotFoundError(f"path is not a file: '{path}'")
    if path.suffix.lower() != ".csv":
        logger.warning("Unexpected extension for '%s'; expected '.csv'", path)


class CsvSalesReader:
    """Reads and validates sales from CSV files. Implements ``SalesSource``."""

    def __init__(self, encoding: str = CSV_ENCODING) -> None:
        self._encoding = encoding

    def read(self, path: Path) -> list[Sale]:
        validate_path(path)
        logger.info("Reading sales from '%s'", path)
        try:
            with path.open(newline="", encoding=self._encoding) as stream:
                sales = _read_stream(stream, path)
        except FileNotFoundError as exc:
            raise InputFileNotFoundError(f"file not found: '{path}'") from exc
        except UnicodeDecodeError as exc:
            raise InvalidCsvError(
                f"'{path}': invalid encoding, use UTF-8"
            ) from exc
        except OSError as exc:
            raise SalesError(f"could not read '{path}': {exc}") from exc

        logger.info("Read %d sale(s) from '%s'", len(sales), path)
        return sales


def _read_stream(stream: TextIO, source: Path) -> list[Sale]:
    reader = csv.DictReader(stream)
    fieldnames = reader.fieldnames
    if not fieldnames:
        raise InvalidCsvError(f"'{source}': empty file or missing header")

    reader.fieldnames = [name.strip().lower() for name in fieldnames]
    _validate_columns(reader.fieldnames, source)

    sales: list[Sale] = []
    try:
        for row in reader:
            sales.append(_convert_row(row, reader.line_num))
    except csv.Error as exc:
        raise InvalidCsvError(
            f"'{source}': malformed CSV after line {reader.line_num}: {exc}"
        ) from exc
    return sales


def _validate_columns(fieldnames: Sequence[str], source: Path) -> None:
    missing = [
        column for column in REQUIRED_COLUMNS if column not in fieldnames
    ]
    if missing:
        raise InvalidCsvError(
            f"'{source}': missing required columns: {', '.join(missing)}"
        )


def _convert_row(
    row: Mapping[str | None, str | None], line_number: int
) -> Sale:
    if None in row:
        raise InvalidCsvError(
            f"line {line_number}: more values than header columns"
        )

    fields = {name: (row.get(name) or "").strip() for name in REQUIRED_COLUMNS}
    empty = [name for name, value in fields.items() if not value]
    if empty:
        raise InvalidCsvError(
            f"line {line_number}: empty or missing fields: {', '.join(empty)}"
        )

    raw_date = fields[COLUMN_DATE]
    try:
        sale_date = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise InvalidCsvError(
            f"line {line_number}: invalid date '{raw_date}' "
            f"(use {DATE_FORMAT})"
        ) from exc

    raw_quantity = fields[COLUMN_QUANTITY]
    try:
        quantity = int(raw_quantity)
    except ValueError as exc:
        raise InvalidCsvError(
            f"line {line_number}: invalid quantity '{raw_quantity}' "
            "(use an integer)"
        ) from exc
    if quantity < 0:
        raise InvalidCsvError(
            f"line {line_number}: quantity cannot be negative"
        )

    raw_unit_price = fields[COLUMN_UNIT_PRICE]
    try:
        unit_price = Decimal(raw_unit_price)
    except InvalidOperation as exc:
        raise InvalidCsvError(
            f"line {line_number}: invalid unit_price '{raw_unit_price}' "
            "(use a dot as the decimal separator)"
        ) from exc
    if not unit_price.is_finite() or unit_price < 0:
        raise InvalidCsvError(
            f"line {line_number}: unit_price must be a non-negative number"
        )

    return Sale(
        sale_date=sale_date,
        product=fields[COLUMN_PRODUCT],
        quantity=quantity,
        unit_price=unit_price,
    )
