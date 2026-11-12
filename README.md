# sales-cli — Advanced Sales Report Generator

A Python CLI that reads a sales CSV file and generates a report with:

- total sales per product;
- grand total value;
- top-selling product;
- filtering by date range.

The output can be a readable text table (`--format text`) or JSON (`--format json`).

## Requirements

- Python **3.10 or newer**
- [uv](https://docs.astral.sh/uv/) to manage the environment and dependencies
- No runtime dependencies (standard library only)
- Development dependencies (`pytest`, `pytest-cov`, `mypy`) are declared in the `dev` dependency group

## Installation

From the project root, create the environment and install the project with its development dependencies:

```bash
uv sync
```

`uv` creates the `.venv/` directory automatically and installs the project in editable mode.

To install the `sales-cli` command globally, without activating any environment:

```bash
uv tool install .
sales-cli --help
```

To run the command from the project without installing it globally:

```bash
uv run sales-cli --help
```

## Development

```bash
uv run pytest      # tests with coverage (minimum 80%)
uv run mypy        # strict type checking
```

## CSV format

The file must be UTF-8 (a BOM is accepted) and contain the header below, in any column order:

| Column           | Type                              | Example      |
|------------------|-----------------------------------|--------------|
| `data`           | Date in `YYYY-MM-DD` format       | `2025-01-05` |
| `produto`        | Non-empty text                    | `Notebook`   |
| `quantidade`     | Non-negative integer              | `2`          |
| `valor_unitario` | Non-negative decimal, dot separator | `4500.00`  |

Header names are normalized (spaces and letter case are ignored). Extra columns cause an error.

> The column names are kept in Portuguese on purpose, so existing CSV files keep working.

Example (`examples/vendas.csv`):

```csv
data,produto,quantidade,valor_unitario
2025-01-05,Notebook,2,4500.00
2025-01-10,Mouse,10,89.90
2025-02-03,Teclado,5,250.00
2025-02-14,Monitor,3,1200.00
2025-03-20,Mouse,15,89.90
2025-03-28,Notebook,1,4300.00
2025-04-02,Headset,4,320.50
2025-05-16,Teclado,6,240.00
2025-06-01,Monitor,2,1150.00
```

## Usage

General syntax:

```text
sales-cli CSV [--format {text,json}] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--log-level LEVEL]
```

| Option        | Description                                                  | Default   |
|---------------|--------------------------------------------------------------|-----------|
| `CSV`         | Path to the sales CSV file                                   | —         |
| `--format`    | Output format: `text` (table) or `json`                      | `text`    |
| `--start`     | Start date of the filter (inclusive)                         | —         |
| `--end`       | End date of the filter (inclusive)                           | —         |
| `--log-level` | Log level on stderr: `DEBUG`, `INFO`, `WARNING`, `ERROR`     | `WARNING` |

### Example 1: text report

```bash
$ sales-cli examples/vendas.csv --format text
```

```text
SALES REPORT
Period: all records
Records considered: 9

Product   Quantity   Total Value
--------  --------  ------------
Notebook         3  R$ 13.300,00
Monitor          5   R$ 5.900,00
Teclado         11   R$ 2.690,00
Mouse           25   R$ 2.247,50
Headset          4   R$ 1.282,00
--------  --------  ------------
TOTAL           48  R$ 25.419,50

Top-selling product: Mouse (25 units)
```

### Example 2: JSON report with a date filter

```bash
$ sales-cli examples/vendas.csv --format json --start 2025-01-01 --end 2025-03-31
```

```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-03-31"
  },
  "total_records": 6,
  "total_quantity": 36,
  "total_value": "20397.50",
  "top_product": {
    "product": "Mouse",
    "total_quantity": 25,
    "total_value": "2247.50"
  },
  "products": [
    {
      "product": "Notebook",
      "total_quantity": 3,
      "total_value": "13300.00"
    },
    {
      "product": "Monitor",
      "total_quantity": 3,
      "total_value": "3600.00"
    },
    {
      "product": "Mouse",
      "total_quantity": 25,
      "total_value": "2247.50"
    },
    {
      "product": "Teclado",
      "total_quantity": 5,
      "total_value": "1250.00"
    }
  ]
}
```

Monetary values in JSON are strings with two decimal places, to avoid floating-point rounding errors.

### Logs and exit codes

- The report is written to **stdout** and logs go to **stderr**, so the output can be redirected safely (`> report.json`).
- Use `--log-level INFO` or `--log-level DEBUG` to follow the execution flow.

| Code | Meaning                                                                  |
|------|--------------------------------------------------------------------------|
| `0`  | Report generated successfully (including when no sales match the period) |
| `1`  | Runtime error: missing file, malformed CSV or invalid data               |
| `2`  | Usage error: invalid argument, malformed date or inverted period         |

## Tests

```bash
uv run pytest
```

The pytest settings live in `[tool.pytest.ini_options]` in `pyproject.toml`. They enable a coverage report and require **at least 80%** coverage of `src/sales_cli`.

The package can also be run as a module:

```bash
uv run python -m sales_cli.main examples/vendas.csv
```

## Type checking

```bash
uv run mypy
```

The configuration uses `strict = true` (see `pyproject.toml`).

## Project structure

```text
.
├── examples/
│   └── vendas.csv          # Sample input file
├── src/
│   └── sales_cli/
│       ├── __init__.py          # Package version
│       ├── main.py              # Composition root: builds dependencies and runs the CLI
│       ├── cli/                 # Presentation layer
│       │   ├── app.py           # Application flow (receives service and renderers)
│       │   ├── arguments.py     # argparse definition and validation
│       │   ├── logs.py          # Logging configuration
│       │   └── output.py        # Text table and JSON renderers
│       ├── core/                # Business rules (no I/O)
│       │   ├── models.py        # Sale, ProductSummary, Report
│       │   ├── ports.py         # SalesSource interface (Protocol)
│       │   ├── rules.py         # Period validation, filtering, totals per product
│       │   └── service.py       # ReportService (receives a SalesSource)
│       ├── errors/              # Application-specific exceptions
│       ├── parsers/             # Input adapters
│       │   └── csv_reader.py    # CsvSalesReader (implements SalesSource)
│       └── py.typed             # Marks the package as typed (PEP 561)
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_core.py
│   ├── test_output.py
│   └── test_parsers.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## License

MIT
