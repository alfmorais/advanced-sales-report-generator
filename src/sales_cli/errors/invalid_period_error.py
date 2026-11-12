"""Exception raised when the requested date range is inconsistent."""

from sales_cli.errors.sales_error import SalesError


class InvalidPeriodError(SalesError):
    """The requested date range is inconsistent."""
