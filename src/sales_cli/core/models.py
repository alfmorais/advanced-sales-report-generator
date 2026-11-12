"""Domain models and monetary helpers."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

ZERO: Final = Decimal("0")
CENT: Final = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Sale:
    """A single sale record."""

    sale_date: date
    product: str
    quantity: int
    unit_price: Decimal

    @property
    def total_value(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True, slots=True)
class ProductSummary:
    """Aggregated totals for a single product."""

    product: str
    total_quantity: int
    total_value: Decimal


@dataclass(frozen=True, slots=True)
class Report:
    """Consolidated result of processing the sales."""

    start_date: date | None
    end_date: date | None
    total_records: int
    total_quantity: int
    total_value: Decimal
    products: tuple[ProductSummary, ...]

    @property
    def top_product(self) -> ProductSummary | None:
        """Product with the highest quantity (ties: value, then name)."""
        if not self.products:
            return None

        return min(
            self.products,
            key=lambda summary: (
                -summary.total_quantity,
                -summary.total_value,
                summary.product,
            ),
        )


def quantize_amount(amount: Decimal) -> Decimal:
    """Round a monetary amount to two decimal places."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
