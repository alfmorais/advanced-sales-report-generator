"""Report service: loads sales from an injected source."""

import logging
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from sales_cli.core.models import ZERO, Report, Sale
from sales_cli.core.ports import SalesSource
from sales_cli.core.rules import filter_by_period, totals_by_product

logger = logging.getLogger(__name__)


def build_report(
    sales: Iterable[Sale],
    start: date | None = None,
    end: date | None = None,
) -> Report:
    """Filter the sales by period and compute the report totals."""
    logger.info("Building report (start=%s, end=%s)", start, end)
    filtered = filter_by_period(sales, start, end)
    if not filtered:
        logger.warning("No sales found for the given period")

    report = Report(
        start_date=start,
        end_date=end,
        total_records=len(filtered),
        total_quantity=sum(sale.quantity for sale in filtered),
        total_value=sum((sale.total_value for sale in filtered), ZERO),
        products=tuple(totals_by_product(filtered)),
    )
    logger.info(
        "Report built: %d record(s), %d product(s)",
        report.total_records,
        len(report.products),
    )
    return report


class ReportService:
    """Generates reports from sales read through an injected source."""

    def __init__(self, sales_source: SalesSource) -> None:
        self._sales_source = sales_source

    def generate(
        self,
        path: Path,
        start: date | None = None,
        end: date | None = None,
    ) -> Report:
        sales = self._sales_source.read(path)
        return build_report(sales, start, end)
