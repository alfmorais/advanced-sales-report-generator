"""Application flow: parse arguments, generate the report and print it."""

import logging
from collections.abc import Mapping, Sequence
from typing import Final

from sales_cli.cli.arguments import parse_arguments
from sales_cli.cli.logs import configure_logging
from sales_cli.cli.output import Renderer
from sales_cli.core.service import ReportService
from sales_cli.errors import SalesError

logger = logging.getLogger(__name__)

EXIT_OK: Final = 0
EXIT_ERROR: Final = 1


def run(
    argv: Sequence[str] | None,
    service: ReportService,
    renderers: Mapping[str, Renderer],
) -> int:
    """Run the CLI with injected collaborators and return the exit code."""
    arguments = parse_arguments(argv, tuple(renderers))
    configure_logging(arguments.log_level)
    logger.debug("Arguments: %s", arguments)

    try:
        report = service.generate(
            arguments.path, arguments.start, arguments.end
        )
    except SalesError as exc:
        logger.error("Failed to generate report: %s", exc)
        return EXIT_ERROR

    print(renderers[arguments.output_format](report))
    logger.info("Report written in '%s' format", arguments.output_format)
    return EXIT_OK
