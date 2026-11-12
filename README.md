# sales-cli — Gerador Avançado de Relatórios de Vendas

Uma CLI em Python que lê um arquivo CSV de vendas e gera um relatório com:

- total de vendas por produto;
- valor total geral;
- produto mais vendido;
- filtragem por intervalo de datas.

A saída pode ser uma tabela de texto legível (`--format text`) ou JSON (`--format json`).

## Requisitos

- Python **3.10 ou superior**
- [uv](https://docs.astral.sh/uv/) para gerenciar o ambiente e as dependências
- Nenhuma dependência de execução (apenas a biblioteca padrão)
- As dependências de desenvolvimento (`pytest`, `pytest-cov`, `mypy`) são declaradas no grupo de dependências `dev`

## Instalação

A partir da raiz do projeto, crie o ambiente e instale o projeto com suas dependências de desenvolvimento:

```bash
uv sync
```

O `uv` cria o diretório `.venv/` automaticamente e instala o projeto em modo editável.

Para instalar o comando `sales-cli` globalmente, sem ativar nenhum ambiente:

```bash
uv tool install .
sales-cli --help
```

Para executar o comando a partir do projeto sem instalá-lo globalmente:

```bash
uv run sales-cli --help
```

## Desenvolvimento

```bash
uv run pytest      # testes com cobertura (mínimo de 80%)
uv run mypy        # verificação de tipos em modo estrito
```

## Formato do CSV

O arquivo deve estar em UTF-8 (um BOM é aceito) e conter o cabeçalho abaixo, em qualquer ordem de colunas:

| Coluna           | Tipo                                      | Exemplo      |
|------------------|-------------------------------------------|--------------|
| `data`           | Data no formato `AAAA-MM-DD`              | `2025-01-05` |
| `produto`        | Texto não vazio                           | `Notebook`   |
| `quantidade`     | Inteiro não negativo                      | `2`          |
| `valor_unitario` | Decimal não negativo, com ponto como separador | `4500.00` |

Os nomes do cabeçalho são normalizados (espaços e maiúsculas/minúsculas são ignorados). Colunas extras geram erro.

> Os nomes das colunas foram mantidos em português de propósito, para que os arquivos CSV existentes continuem funcionando.

Exemplo (`examples/vendas.csv`):

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

## Uso

Sintaxe geral:

```text
sales-cli CSV [--format {text,json}] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--log-level NÍVEL]
```

| Opção         | Descrição                                                         | Padrão    |
|---------------|-------------------------------------------------------------------|-----------|
| `CSV`         | Caminho para o arquivo CSV de vendas                              | —         |
| `--format`    | Formato de saída: `text` (tabela) ou `json`                       | `text`    |
| `--start`     | Data inicial do filtro (inclusiva)                                | —         |
| `--end`       | Data final do filtro (inclusiva)                                  | —         |
| `--log-level` | Nível de log no stderr: `DEBUG`, `INFO`, `WARNING`, `ERROR`       | `WARNING` |

### Exemplo 1: relatório em texto

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

### Exemplo 2: relatório em JSON com filtro de data

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

Os valores monetários em JSON são strings com duas casas decimais, para evitar erros de arredondamento de ponto flutuante.

### Logs e códigos de saída

- O relatório é escrito na **stdout** e os logs vão para a **stderr**, então a saída pode ser redirecionada com segurança (`> report.json`).
- Use `--log-level INFO` ou `--log-level DEBUG` para acompanhar o fluxo de execução.

| Código | Significado                                                                                  |
|--------|----------------------------------------------------------------------------------------------|
| `0`    | Relatório gerado com sucesso (inclusive quando nenhuma venda corresponde ao período)         |
| `1`    | Erro de execução: arquivo ausente, CSV malformado ou dados inválidos                         |
| `2`    | Erro de uso: argumento inválido, data malformada ou período invertido                        |

## Testes

```bash
uv run pytest
```

As configurações do pytest ficam em `[tool.pytest.ini_options]` no `pyproject.toml`. Elas habilitam o relatório de cobertura e exigem **no mínimo 80%** de cobertura de `src/sales_cli`.

O pacote também pode ser executado como módulo:

```bash
uv run python -m sales_cli.main examples/vendas.csv
```

## Verificação de tipos

```bash
uv run mypy
```

A configuração usa `strict = true` (veja `pyproject.toml`).

## Estrutura do projeto

```text
.
├── examples/
│   └── vendas.csv          # Arquivo de entrada de exemplo
├── src/
│   └── sales_cli/
│       ├── __init__.py          # Versão do pacote
│       ├── main.py              # Raiz de composição: monta as dependências e executa a CLI
│       ├── cli/                 # Camada de apresentação
│       │   ├── app.py           # Fluxo da aplicação (recebe o serviço e os renderizadores)
│       │   ├── arguments.py     # Definição e validação do argparse
│       │   ├── logs.py          # Configuração de logs
│       │   └── output.py        # Renderizadores de tabela de texto e JSON
│       ├── core/                # Regras de negócio (sem I/O)
│       │   ├── models.py        # Sale, ProductSummary, Report
│       │   ├── ports.py         # Interface SalesSource (Protocol)
│       │   ├── rules.py         # Validação de período, filtragem, totais por produto
│       │   └── service.py       # ReportService (recebe um SalesSource)
│       ├── errors/              # Exceções específicas da aplicação
│       ├── parsers/             # Adaptadores de entrada
│       │   └── csv_reader.py    # CsvSalesReader (implementa SalesSource)
│       └── py.typed             # Marca o pacote como tipado (PEP 561)
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

## Licença

MIT
