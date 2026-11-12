"""Pure business rules: period validation, filtering and aggregation."""

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from sales_cli.core.models import ZERO, ProductSummary, Sale
from sales_cli.errors import InvalidPeriodError


def validate_period(start: date | None, end: date | None) -> None:
    """Ensure the start date is not after the end date."""
    if start is not None and end is not None and start > end:
        raise InvalidPeriodError(
            f"start date ({start.isoformat()}) is after end date "
            f"({end.isoformat()})"
        )


def filter_by_period(
    sales: Iterable[Sale],
    start: date | None = None,
    end: date | None = None,
) -> list[Sale]:
    """Return the sales within [start, end], with both bounds inclusive."""
    validate_period(start, end)
    return [
        sale
        for sale in sales
        if (start is None or sale.sale_date >= start)
        and (end is None or sale.sale_date <= end)
    ]


def totals_by_product(sales: Iterable[Sale]) -> list[ProductSummary]:
    """Sum quantity and value per product, sorted by value (descending)."""
    quantities: dict[str, int] = {}
    values: dict[str, Decimal] = {}
    for sale in sales:
        quantities[sale.product] = (
            quantities.get(sale.product, 0) + sale.quantity
        )
        values[sale.product] = (
            values.get(sale.product, ZERO) + sale.total_value
        )

    summaries = [
        ProductSummary(
            product=product,
            total_quantity=quantities[product],
            total_value=values[product],
        )
        for product in quantities
    ]
    return sorted(
        summaries, key=lambda summary: (-summary.total_value, summary.product)
    )
