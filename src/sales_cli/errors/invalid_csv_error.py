"""Exception raised when the CSV content is malformed or invalid."""

from sales_cli.errors.sales_error import SalesError


class InvalidCsvError(SalesError):
    """The CSV content is malformed or contains invalid values."""
