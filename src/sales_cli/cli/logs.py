"""Logging configuration for the CLI."""

import logging
import sys
from typing import Final

LOG_FORMAT: Final = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: str) -> None:
    """Send logs to stderr so that stdout only carries the report."""
    logging.basicConfig(format=LOG_FORMAT, stream=sys.stderr)
    logging.getLogger("sales_cli").setLevel(level)
