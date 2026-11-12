"""Tests for the CLI layer: arguments, app flow and end-to-end runs."""

import argparse
import json
import logging
import runpy
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

from sales_cli.cli.app import EXIT_ERROR, EXIT_OK, run
from sales_cli.cli.arguments import (
    Arguments,
    create_parser,
    parse_arguments,
    parse_date,
)
from sales_cli.cli.output import format_text
from sales_cli.core.models import Report, Sale
from sales_cli.core.service import ReportService
from sales_cli.errors import InvalidCsvError
from sales_cli.main import main

WriteCsv = Callable[..., Path]
EXIT_USAGE = 2
Q1_RECORDS = 6
ALL_RECORDS = 9


class FakeSalesSource:
    """Test double for the ``SalesSource`` port."""

    def __init__(
        self, sales: list[Sale] | None = None, error: Exception | None = None
    ) -> None:
        self.sales = sales or []
        self.error = error

    def read(self, path: Path) -> list[Sale]:
        if self.error is not None:
            raise self.error
        return list(self.sales)


@pytest.mark.parametrize("value", ["2025-01-31", "2024-02-29"])
def test_parse_date_accepts_valid_dates(value: str) -> None:
    assert parse_date(value) == date.fromisoformat(value)


@pytest.mark.parametrize(
    "value", ["31/01/2025", "2025-13-01", "2025-02-30", "", "abc"]
)
def test_parse_date_rejects_invalid_dates(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="YYYY-MM-DD"):
        parse_date(value)


def test_parse_arguments_defaults() -> None:
    assert parse_arguments(["sales.csv"]) == Arguments(
        path=Path("sales.csv"),
        output_format="text",
        start=None,
        end=None,
        log_level="WARNING",
    )


def test_parse_arguments_with_all_options() -> None:
    arguments = parse_arguments([
        "sales.csv",
        "--format",
        "json",
        "--start",
        "2025-01-01",
        "--end",
        "2025-03-31",
        "--log-level",
        "DEBUG",
    ])

    assert arguments.output_format == "json"
    assert arguments.start == date(2025, 1, 1)
    assert arguments.end == date(2025, 3, 31)
    assert arguments.log_level == "DEBUG"


def test_parse_arguments_choices_follow_injected_formats() -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(
            ["sales.csv", "--format", "json"], output_formats=("text", "csv")
        )
    assert excinfo.value.code == EXIT_USAGE


def test_parse_arguments_rejects_malformed_date() -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(["sales.csv", "--start", "01/01/2025"])
    assert excinfo.value.code == EXIT_USAGE


def test_parse_arguments_rejects_inverted_period(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments([
            "sales.csv",
            "--start",
            "2025-03-01",
            "--end",
            "2025-01-01",
        ])
    assert excinfo.value.code == EXIT_USAGE
    assert "is after end date" in capsys.readouterr().err


def test_parse_arguments_requires_file() -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments([])
    assert excinfo.value.code == EXIT_USAGE


def test_create_parser_uses_sales_cli_prog() -> None:
    assert create_parser().prog == "sales-cli"


def test_run_uses_injected_renderer_and_service(
    sales: list[Sale], capsys: pytest.CaptureFixture[str]
) -> None:
    service = ReportService(FakeSalesSource(sales))
    renderers = {"fake": lambda report: f"records={report.total_records}"}

    exit_code = run(
        ["any.csv", "--format", "fake"], service=service, renderers=renderers
    )

    assert exit_code == EXIT_OK
    assert capsys.readouterr().out.strip() == "records=9"


def test_run_returns_error_when_source_fails(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    service = ReportService(FakeSalesSource(error=InvalidCsvError("broken")))

    with caplog.at_level(logging.ERROR, logger="sales_cli"):
        exit_code = run(
            ["any.csv"], service=service, renderers={"text": format_text}
        )

    assert exit_code == EXIT_ERROR
    assert "broken" in caplog.text
    assert not capsys.readouterr().out


def test_main_text_format(
    sample_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(sample_csv), "--format", "text"])

    output = capsys.readouterr().out
    assert exit_code == EXIT_OK
    assert "SALES REPORT" in output
    assert "Period: all records" in output
    assert "R$ 25.419,50" in output
    assert "Top-selling products: Mouse (25 units)" in output


def test_main_defaults_to_text_format(
    sample_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(sample_csv)]) == EXIT_OK
    assert "SALES REPORT" in capsys.readouterr().out


def test_main_json_format_with_period(
    sample_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([
        str(sample_csv),
        "--format",
        "json",
        "--start",
        "2025-01-01",
        "--end",
        "2025-03-31",
    ])

    document = json.loads(capsys.readouterr().out)
    assert exit_code == EXIT_OK
    assert document["period"] == {"start": "2025-01-01", "end": "2025-03-31"}
    assert document["total_records"] == Q1_RECORDS
    assert document["total_value"] == "20397.50"


def test_main_period_without_sales_is_not_an_error(
    sample_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(sample_csv), "--start", "2030-01-01"])

    assert exit_code == EXIT_OK
    assert "No sales found for the given period." in capsys.readouterr().out


def test_main_missing_file_returns_error(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="sales_cli"):
        exit_code = main([str(tmp_path / "missing.csv")])

    assert exit_code == EXIT_ERROR
    assert "file not found" in caplog.text


def test_main_invalid_csv_returns_error(
    write_csv: WriteCsv, caplog: pytest.LogCaptureFixture
) -> None:
    path = write_csv(
        "data,produto,quantidade,valor_unitario\n2025-99-99,A,1,1\n"
    )

    with caplog.at_level(logging.ERROR, logger="sales_cli"):
        exit_code = main([str(path)])

    assert exit_code == EXIT_ERROR
    assert "invalid date" in caplog.text


def test_main_invalid_date_exits_with_usage_error(
    sample_csv: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([str(sample_csv), "--start", "2025/01/01"])

    assert excinfo.value.code == EXIT_USAGE
    assert "YYYY-MM-DD" in capsys.readouterr().err


def test_main_reads_sys_argv_when_no_argv_given(
    sample_csv: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["sales-cli", str(sample_csv), "--format", "json"]
    )

    assert main() == EXIT_OK
    assert json.loads(capsys.readouterr().out)["total_records"] == ALL_RECORDS


def test_run_as_module(
    sample_csv: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["sales_cli", str(sample_csv)])
    monkeypatch.delitem(sys.modules, "sales_cli.main")

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("sales_cli.main", run_name="__main__")

    assert excinfo.value.code == EXIT_OK
    assert "SALES REPORT" in capsys.readouterr().out


def test_report_type_is_used_by_renderers(sales: list[Sale]) -> None:
    report: Report = ReportService(FakeSalesSource(sales)).generate(
        Path("any.csv")
    )
    assert format_text(report).startswith("SALES REPORT")
