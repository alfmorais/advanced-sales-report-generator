"""Tests for the output formatting (sales_cli.cli.output)."""

import json
from datetime import date
from decimal import Decimal

import pytest

from sales_cli.cli.output import format_currency, format_json, format_text
from sales_cli.core.models import ProductSummary, Report, Sale
from sales_cli.core.service import build_report

Q1_RECORDS = 6
Q1_QUANTITY = 36


@pytest.fixture
def first_quarter_report(sales: list[Sale]) -> Report:
    return build_report(sales, date(2025, 1, 1), date(2025, 3, 31))


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("20397.5"), "R$ 20.397,50"),
        (Decimal("0"), "R$ 0,00"),
        (Decimal("1234.567"), "R$ 1.234,57"),
        (Decimal("999.999"), "R$ 1.000,00"),
        (Decimal("1000000"), "R$ 1.000.000,00"),
        (Decimal("-1500"), "R$ -1.500,00"),
    ],
)
def test_format_currency(amount: Decimal, expected: str) -> None:
    assert format_currency(amount) == expected


def test_format_text_contains_table_and_summary(
    first_quarter_report: Report,
) -> None:
    text = format_text(first_quarter_report)

    assert text.startswith("SALES REPORT")
    assert "Period: 2025-01-01 to 2025-03-31" in text
    assert "Records considered: 6" in text
    assert "Product" in text
    assert "Quantity" in text
    assert "Total Value" in text
    assert "Notebook" in text
    assert "R$ 13.300,00" in text
    assert "TOTAL" in text
    assert "R$ 20.397,50" in text
    assert "Top-selling products: Mouse (25 units)" in text


def test_format_text_aligns_columns(first_quarter_report: Report) -> None:
    lines = format_text(first_quarter_report).splitlines()
    table_lines = [line for line in lines if "R$" in line]

    assert len({len(line) for line in table_lines}) == 1


def test_format_text_without_sales() -> None:
    report = build_report([], date(2025, 1, 1), date(2025, 1, 31))

    text = format_text(report)

    assert "No sales found for the given period." in text
    assert "TOTAL" not in text
    assert "Top-selling" not in text


@pytest.mark.parametrize(
    ("start", "end", "description"),
    [
        (None, None, "all records"),
        (date(2025, 1, 1), None, "from 2025-01-01"),
        (None, date(2025, 3, 31), "until 2025-03-31"),
    ],
)
def test_format_text_describes_period(
    start: date | None, end: date | None, description: str
) -> None:
    report = Report(start, end, 0, 0, Decimal("0"), ())

    assert f"Period: {description}" in format_text(report)


def test_format_json_full_structure(first_quarter_report: Report) -> None:
    document = json.loads(format_json(first_quarter_report))

    assert document["period"] == {"start": "2025-01-01", "end": "2025-03-31"}
    assert document["total_records"] == Q1_RECORDS
    assert document["total_quantity"] == Q1_QUANTITY
    assert document["total_value"] == "20397.50"
    assert document["top_product"] == {
        "product": "Mouse",
        "total_quantity": 25,
        "total_value": "2247.50",
    }
    products = document["products"]
    assert [product["product"] for product in products] == [
        "Notebook",
        "Monitor",
        "Mouse",
        "Teclado",
    ]
    assert products[0] == {
        "product": "Notebook",
        "total_quantity": 3,
        "total_value": "13300.00",
    }


def test_format_json_without_sales() -> None:
    document = json.loads(format_json(build_report([], None, None)))

    assert document["period"] == {"start": None, "end": None}
    assert document["top_product"] is None
    assert document["products"] == []
    assert document["total_value"] == "0.00"


def test_format_json_preserves_accents() -> None:
    report = Report(
        None,
        None,
        1,
        1,
        Decimal("10"),
        (ProductSummary("Câmera", 1, Decimal("10")),),
    )

    assert "Câmera" in format_json(report)
