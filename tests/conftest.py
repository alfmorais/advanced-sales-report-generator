"""Fixtures shared across the test suite."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from sales_cli.core.models import Sale

HEADER = "data,produto,quantidade,valor_unitario\n"


@pytest.fixture
def sales() -> list[Sale]:
    """Sales from 2025 used as the reference dataset in the tests."""
    return [
        Sale(date(2025, 1, 5), "Notebook", 2, Decimal("4500.00")),
        Sale(date(2025, 1, 10), "Mouse", 10, Decimal("89.90")),
        Sale(date(2025, 2, 3), "Teclado", 5, Decimal("250.00")),
        Sale(date(2025, 2, 14), "Monitor", 3, Decimal("1200.00")),
        Sale(date(2025, 3, 20), "Mouse", 15, Decimal("89.90")),
        Sale(date(2025, 3, 28), "Notebook", 1, Decimal("4300.00")),
        Sale(date(2025, 4, 2), "Headset", 4, Decimal("320.50")),
        Sale(date(2025, 5, 16), "Teclado", 6, Decimal("240.00")),
        Sale(date(2025, 6, 1), "Monitor", 2, Decimal("1150.00")),
    ]


@pytest.fixture
def write_csv(tmp_path: Path) -> Callable[..., Path]:
    """Create a temporary CSV file with the given content."""

    def _write(content: str | bytes, name: str = "sales.csv") -> Path:
        path = tmp_path / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def sample_csv(write_csv: Callable[..., Path]) -> Path:
    """Valid CSV containing the same sales as the ``sales`` fixture."""
    content = (
        HEADER
        + "2025-01-05,Notebook,2,4500.00\n"
        + "2025-01-10,Mouse,10,89.90\n"
        + "2025-02-03,Teclado,5,250.00\n"
        + "2025-02-14,Monitor,3,1200.00\n"
        + "2025-03-20,Mouse,15,89.90\n"
        + "2025-03-28,Notebook,1,4300.00\n"
        + "2025-04-02,Headset,4,320.50\n"
        + "2025-05-16,Teclado,6,240.00\n"
        + "2025-06-01,Monitor,2,1150.00\n"
    )
    return write_csv(content, "sample.csv")
