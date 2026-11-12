"""Tests for the CSV adapter (sales_cli.parsers.csv_reader)."""

import logging
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

import pytest

from sales_cli.errors import (
    InputFileNotFoundError,
    InvalidCsvError,
    SalesError,
)
from sales_cli.parsers.csv_reader import CsvSalesReader, validate_path

HEADER = "data,produto,quantidade,valor_unitario\n"
WriteCsv = Callable[..., Path]
SAMPLE_SALES_COUNT = 2
NOTEBOOK_QUANTITY = 2


@pytest.fixture
def reader() -> CsvSalesReader:
    return CsvSalesReader()


def test_validate_path_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InputFileNotFoundError, match="file not found"):
        validate_path(tmp_path / "missing.csv")


def test_validate_path_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(InputFileNotFoundError, match="not a file"):
        validate_path(tmp_path)


def test_validate_path_accepts_existing_file(write_csv: WriteCsv) -> None:
    validate_path(write_csv(HEADER))


def test_validate_path_warns_on_unexpected_extension(
    write_csv: WriteCsv, caplog: pytest.LogCaptureFixture
) -> None:
    path = write_csv(HEADER, "sales.txt")
    with caplog.at_level(
        logging.WARNING, logger="sales_cli.parsers.csv_reader"
    ):
        validate_path(path)
    assert "Unexpected extension" in caplog.text


def test_read_valid_file(reader: CsvSalesReader, write_csv: WriteCsv) -> None:
    path = write_csv(
        HEADER + "2025-01-05,Notebook,2,4500.00\n2025-01-10,Mouse,10,89.9\n"
    )

    sales = reader.read(path)

    assert len(sales) == SAMPLE_SALES_COUNT
    assert sales[0].sale_date == date(2025, 1, 5)
    assert sales[0].product == "Notebook"
    assert sales[0].quantity == NOTEBOOK_QUANTITY
    assert sales[0].unit_price == Decimal("4500.00")
    assert sales[1].unit_price == Decimal("89.9")


def test_read_normalizes_header_and_spaces(
    reader: CsvSalesReader, write_csv: WriteCsv
) -> None:
    content = (
        " DATA , Produto ,QUANTIDADE,valor_unitario\n"
        "2025-01-05, Notebook ,2,10\n"
    )

    sales = reader.read(write_csv(content))

    assert sales[0].product == "Notebook"
    assert sales[0].quantity == NOTEBOOK_QUANTITY


def test_read_accepts_utf8_bom(
    reader: CsvSalesReader, write_csv: WriteCsv
) -> None:
    content = "\ufeff" + HEADER + "2025-01-05,Café,1,10\n"

    assert reader.read(write_csv(content))[0].product == "Café"


def test_read_empty_file(reader: CsvSalesReader, write_csv: WriteCsv) -> None:
    with pytest.raises(InvalidCsvError, match="empty file"):
        reader.read(write_csv(""))


def test_read_missing_required_columns(
    reader: CsvSalesReader, write_csv: WriteCsv
) -> None:
    with pytest.raises(InvalidCsvError, match="quantidade, valor_unitario"):
        reader.read(write_csv("data,produto\n2025-01-05,Notebook\n"))


@pytest.mark.parametrize(
    ("row", "fragment"),
    [
        ("31/01/2025,Notebook,2,10", "invalid date"),
        ("2025-01-05,Notebook,dois,10", "invalid quantity"),
        ("2025-01-05,Notebook,1.5,10", "invalid quantity"),
        ("2025-01-05,Notebook,-1,10", "cannot be negative"),
        ("2025-01-05,Notebook,2,abc", "invalid unit_price"),
        ("2025-01-05,Notebook,2,1,0", "more values"),
        ("2025-01-05,Notebook,2,NaN", "non-negative"),
        ("2025-01-05,Notebook,2,-10", "non-negative"),
        ("2025-01-05,Notebook,2,Infinity", "non-negative"),
        ("2025-01-05,,2,10", "empty or missing"),
        ("2025-01-05,Notebook,2", "empty or missing"),
    ],
)
def test_read_rejects_invalid_rows(
    reader: CsvSalesReader, write_csv: WriteCsv, row: str, fragment: str
) -> None:
    path = write_csv(HEADER + "2025-01-01,Mouse,1,10\n" + row + "\n")

    with pytest.raises(InvalidCsvError, match=f"line 3: .*{fragment}"):
        reader.read(path)


def test_read_reports_last_valid_line_on_csv_error(
    reader: CsvSalesReader, write_csv: WriteCsv
) -> None:
    huge_field = "A" * 200_000
    path = write_csv(HEADER + f"2025-01-01,{huge_field},1,10\n")

    with pytest.raises(InvalidCsvError, match="malformed CSV after line 1"):
        reader.read(path)


def test_read_rejects_invalid_encoding(
    reader: CsvSalesReader, write_csv: WriteCsv
) -> None:
    content = HEADER.encode() + b"2025-01-05,Caf\xe9,1,10\n"

    with pytest.raises(InvalidCsvError, match="UTF-8"):
        reader.read(write_csv(content))


def test_read_missing_file(reader: CsvSalesReader, tmp_path: Path) -> None:
    with pytest.raises(InputFileNotFoundError):
        reader.read(tmp_path / "missing.csv")


def test_read_directory_is_rejected_as_not_a_file(
    reader: CsvSalesReader, tmp_path: Path
) -> None:
    with pytest.raises(InputFileNotFoundError, match="not a file"):
        reader.read(tmp_path)


def test_read_file_removed_before_opening(
    reader: CsvSalesReader,
    write_csv: WriteCsv,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = write_csv(HEADER)

    def _vanish(self: Path, *args: object, **kwargs: object) -> NoReturn:
        raise FileNotFoundError(2, "No such file", str(self))

    monkeypatch.setattr(Path, "open", _vanish)

    with pytest.raises(InputFileNotFoundError, match="file not found"):
        reader.read(path)


def test_read_wraps_unexpected_os_error(
    reader: CsvSalesReader,
    write_csv: WriteCsv,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = write_csv(HEADER)

    def _deny(self: Path, *args: object, **kwargs: object) -> NoReturn:
        raise PermissionError(13, "Permission denied", str(self))

    monkeypatch.setattr(Path, "open", _deny)

    with pytest.raises(SalesError, match="could not read"):
        reader.read(path)
