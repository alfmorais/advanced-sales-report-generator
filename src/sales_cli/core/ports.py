"""Ports: interfaces the core depends on; adapters live outside it."""

from pathlib import Path
from typing import Protocol

from sales_cli.core.models import Sale


class SalesSource(Protocol):
    """Anything able to load sales from a path, e.g. a CSV reader."""

    def read(self, path: Path) -> list[Sale]: ...
