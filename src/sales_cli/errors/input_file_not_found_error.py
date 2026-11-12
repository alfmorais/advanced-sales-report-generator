"""Exception raised when the input file is missing or is not a regular file."""

from sales_cli.errors.sales_error import SalesError


class InputFileNotFoundError(SalesError):
    """The input file does not exist or is not a regular file."""
