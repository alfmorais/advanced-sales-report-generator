"""Tests for the core: models, pure rules and the report service."""

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from sales_cli.core.models import ProductSummary, Report, Sale, quantize_amount
from sales_cli.core.rules import (
    filter_by_period,
    totals_by_product,
    validate_period,
)
from sales_cli.core.service import ReportService, build_report
from sales_cli.errors import InvalidPeriodError

ALL_RECORDS = 9
ALL_QUANTITY = 48
Q1_RECORDS = 6
Q1_QUANTITY = 36
MOUSE_QUANTITY = 25
JANUARY_RECORDS = 2


class FakeSalesSource:
    """Test double for the ``SalesSource`` port."""

    def __init__(self, sales: list[Sale]) -> None:
        self.sales = sales
        self.requested_paths: list[Path] = []

    def read(self, path: Path) -> list[Sale]:
        self.requested_paths.append(path)
        return list(self.sales)


def test_sale_total_value_multiplies_quantity_by_unit_price() -> None:
    sale = Sale(date(2025, 1, 1), "Mouse", 3, Decimal("89.90"))
    assert sale.total_value == Decimal("269.70")


def test_quantize_amount_rounds_half_up() -> None:
    assert quantize_amount(Decimal("1.005")) == Decimal("1.01")
    assert quantize_amount(Decimal("10")) == Decimal("10.00")


def test_validate_period_accepts_missing_or_ordered_bounds() -> None:
    validate_period(None, None)
    validate_period(date(2025, 1, 1), None)
    validate_period(None, date(2025, 1, 1))
    validate_period(date(2025, 1, 1), date(2025, 1, 1))


def test_validate_period_rejects_start_after_end() -> None:
    with pytest.raises(InvalidPeriodError, match="is after end date"):
        validate_period(date(2025, 2, 1), date(2025, 1, 1))


def test_filter_without_bounds_returns_all_sales(sales: list[Sale]) -> None:
    assert filter_by_period(sales) == sales


def test_filter_by_range_includes_both_bounds(sales: list[Sale]) -> None:
    filtered = filter_by_period(sales, date(2025, 1, 10), date(2025, 3, 20))
    assert [sale.sale_date for sale in filtered] == [
        date(2025, 1, 10),
        date(2025, 2, 3),
        date(2025, 2, 14),
        date(2025, 3, 20),
    ]


def test_filter_with_start_only(sales: list[Sale]) -> None:
    filtered = filter_by_period(sales, start=date(2025, 5, 1))
    assert [sale.product for sale in filtered] == ["Teclado", "Monitor"]


def test_filter_with_end_only(sales: list[Sale]) -> None:
    filtered = filter_by_period(sales, end=date(2025, 1, 31))
    assert len(filtered) == JANUARY_RECORDS


def test_filter_with_invalid_period_raises(sales: list[Sale]) -> None:
    with pytest.raises(InvalidPeriodError):
        filter_by_period(sales, date(2025, 6, 1), date(2025, 1, 1))


def test_totals_by_product_aggregates_and_sorts_by_value(
    sales: list[Sale],
) -> None:
    summaries = totals_by_product(sales)

    assert [summary.product for summary in summaries] == [
        "Notebook",
        "Monitor",
        "Teclado",
        "Mouse",
        "Headset",
    ]
    mouse = next(
        summary for summary in summaries if summary.product == "Mouse"
    )
    assert mouse.total_quantity == MOUSE_QUANTITY
    assert mouse.total_value == Decimal("2247.50")


def test_totals_by_product_empty_input() -> None:
    assert totals_by_product([]) == []


def test_top_product_considers_quantity_first() -> None:
    report = Report(
        start_date=None,
        end_date=None,
        total_records=2,
        total_quantity=30,
        total_value=Decimal("100"),
        products=(
            ProductSummary("Expensive", 2, Decimal("90")),
            ProductSummary("Cheap", 28, Decimal("10")),
        ),
    )
    top = report.top_product
    assert top is not None
    assert top.product == "Cheap"


def test_top_product_breaks_ties_by_value_then_name() -> None:
    value_tie = Report(
        None,
        None,
        2,
        10,
        Decimal("30"),
        (
            ProductSummary("Alpha", 5, Decimal("10")),
            ProductSummary("Beta", 5, Decimal("20")),
        ),
    )
    assert value_tie.top_product == ProductSummary("Beta", 5, Decimal("20"))

    full_tie = Report(
        None,
        None,
        2,
        10,
        Decimal("20"),
        (
            ProductSummary("Zeta", 5, Decimal("10")),
            ProductSummary("Alpha", 5, Decimal("10")),
        ),
    )
    assert full_tie.top_product == ProductSummary("Alpha", 5, Decimal("10"))


def test_top_product_is_none_without_products() -> None:
    assert Report(None, None, 0, 0, Decimal("0"), ()).top_product is None


def test_build_report_for_all_records(sales: list[Sale]) -> None:
    report = build_report(sales)

    assert report.total_records == ALL_RECORDS
    assert report.total_quantity == ALL_QUANTITY
    assert report.total_value == Decimal("25419.50")
    assert report.start_date is None
    assert report.end_date is None


def test_build_report_for_first_quarter(sales: list[Sale]) -> None:
    report = build_report(sales, date(2025, 1, 1), date(2025, 3, 31))

    assert report.total_records == Q1_RECORDS
    assert report.total_quantity == Q1_QUANTITY
    assert report.total_value == Decimal("20397.50")
    assert report.start_date == date(2025, 1, 1)
    assert report.end_date == date(2025, 3, 31)
    assert report.top_product == ProductSummary(
        "Mouse", 25, Decimal("2247.50")
    )


def test_build_report_without_results_logs_warning(
    sales: list[Sale], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="sales_cli.core.service"):
        report = build_report(sales, date(2030, 1, 1), date(2030, 12, 31))

    assert report.total_records == 0
    assert report.total_value == Decimal("0")
    assert report.products == ()
    assert "No sales found" in caplog.text


def test_build_report_propagates_invalid_period(sales: list[Sale]) -> None:
    with pytest.raises(InvalidPeriodError):
        build_report(sales, date(2025, 2, 1), date(2025, 1, 1))


def test_report_service_uses_injected_source(sales: list[Sale]) -> None:
    source = FakeSalesSource(sales)

    report = ReportService(source).generate(
        Path("any.csv"), date(2025, 1, 1), date(2025, 3, 31)
    )

    assert source.requested_paths == [Path("any.csv")]
    assert report.total_records == Q1_RECORDS
    assert report.total_value == Decimal("20397.50")
