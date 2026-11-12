"""Report rendering as a plain-text table or as JSON."""

import json
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from sales_cli.core.models import ProductSummary, Report, quantize_amount

Renderer = Callable[[Report], str]
Row = tuple[str, str, str]


def format_currency(amount: Decimal) -> str:
    """Format an amount with Brazilian currency style, e.g. ``R$ 1.234,56``."""
    en_us = f"{quantize_amount(amount):,.2f}"
    pt_br = en_us.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {pt_br}"


def format_text(report: Report) -> str:
    """Render the report as a readable text table."""
    lines: list[str] = [
        "SALES REPORT",
        f"Period: {_describe_period(report)}",
        f"Records considered: {report.total_records}",
        "",
    ]
    top = report.top_product
    if top is None:
        lines.append("No sales found for the given period.")
        return "\n".join(lines)

    header: Row = ("Product", "Quantity", "Total Value")
    body = [_product_row(summary) for summary in report.products]
    footer: Row = (
        "TOTAL",
        str(report.total_quantity),
        format_currency(report.total_value),
    )
    widths = [
        max(len(row[index]) for row in [header, *body, footer])
        for index in range(3)
    ]
    separator = "  ".join("-" * width for width in widths)

    lines.append(_format_line(header, widths))
    lines.append(separator)
    lines.extend(_format_line(row, widths) for row in body)
    lines.append(separator)
    lines.append(_format_line(footer, widths))

    lines.append("")
    lines.append(
        f"Top-selling products: {top.product} ({top.total_quantity} units)"
    )

    return "\n".join(lines)


def format_json(report: Report) -> str:
    """Render the report as JSON. Money values are two-decimal strings."""
    top = report.top_product
    document: dict[str, object] = {
        "period": {
            "start": _iso_or_none(report.start_date),
            "end": _iso_or_none(report.end_date),
        },
        "total_records": report.total_records,
        "total_quantity": report.total_quantity,
        "total_value": str(quantize_amount(report.total_value)),
        "top_product": _summary_to_dict(top) if top is not None else None,
        "products": [_summary_to_dict(summary) for summary in report.products],
    }
    return json.dumps(document, ensure_ascii=False, indent=2)


def _product_row(summary: ProductSummary) -> Row:
    return (
        summary.product,
        str(summary.total_quantity),
        format_currency(summary.total_value),
    )


def _format_line(cells: Row, widths: list[int]) -> str:
    product, quantity, value = cells
    return "  ".join(
        [
            product.ljust(widths[0]),
            quantity.rjust(widths[1]),
            value.rjust(widths[2]),
        ]
    )


def _describe_period(report: Report) -> str:
    start = report.start_date
    end = report.end_date
    if start is not None and end is not None:
        return f"{start.isoformat()} to {end.isoformat()}"
    if start is not None:
        return f"from {start.isoformat()}"
    if end is not None:
        return f"until {end.isoformat()}"
    return "all records"


def _iso_or_none(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _summary_to_dict(summary: ProductSummary) -> dict[str, object]:
    return {
        "product": summary.product,
        "total_quantity": summary.total_quantity,
        "total_value": str(quantize_amount(summary.total_value)),
    }
