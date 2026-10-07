# Name Generator → Sales Analytics (dbt + DuckDB)

**Portfolio project** demonstrating an end-to-end analytics engineering
workflow: synthetic data generation, a version-controlled dbt project,
automated daily orchestration, and tested, documented data models — all
running on a free, local stack (no cloud warehouse required).

## What this demonstrates

- **Data modeling with dbt** — staging → mart layering, `ref()`-based
  lineage, YAML-documented schemas, and automated data tests
  (`unique`, `not_null`, `accepted_values`, `relationships`).
- **SQL** — a standalone migration script (`sql/add_user_id_column.sql`)
  that adds and backfills a new primary key column on an existing table.
- **Python** — reproducible, seeded synthetic data generation with
  [Faker](https://faker.readthedocs.io/) (customers + sales transactions
  modeled loosely on Microsoft's Wide World Importers sample).
- **Pipeline orchestration** — a scheduled job (Windows Task Scheduler)
  that regenerates data and runs `dbt build` every morning, with logging
  and failure handling.
- **Data warehousing basics** — [DuckDB](https://duckdb.org/) as a
  lightweight, file-based analytical database, with a dimensional-style
  customer ↔ sales join and aggregate summary tables.

## Architecture

```
Faker (Python) ──► seeds/*.csv ──► dbt seed ──► DuckDB tables
                                                     │
                                        dbt staging models (views)
                                                     │
                                        dbt mart models (tables)
                                                     │
                      customer_sales ──► customer_sales_summary
                              │
                              └───────► product_sales_summary
```

Each generated "name" record gets a stable `user_id` (UUID), used to join
it against a synthetic `sales_transactions` table — simulating a customer
purchase history use case. Each transaction also references a `product_id`
from a small product catalog (dimension table), so product attributes
(name/category/price) are stored once instead of repeated per transaction.

## Project layout

| Path | Purpose |
|---|---|
| `scripts/generate_names.py` | Generates fake customer records (`user_id`, name, email, demographics) |
| `scripts/generate_products.py` | Generates a static product catalog (`product_id`, name, category, price) |
| `scripts/generate_sales_transactions.py` | Generates synthetic sales transactions tied to a `user_id` and `product_id` |
| `sql/add_user_id_column.sql` | SQL migration: adds/backfills `user_id` on an existing table |
| `seeds/` | Raw CSV data loaded into DuckDB via `dbt seed` |
| `models/staging/` | Cleaned/typed views over raw seeds (`stg_names`, `stg_products`, `stg_sales_transactions`) |
| `models/marts/` | Business-facing tables: demographic summaries, customer-sales-product join, customer lifetime value, product performance |
| `scripts/daily_run.ps1` | Daily automation: regenerate data → `dbt build` |
| `scripts/register_scheduled_task.ps1` | Registers the Windows Task Scheduler job |
| `data/name_generator.duckdb` | The DuckDB database file (git-ignored) |

## Try it yourself

```bash
python -m pip install dbt-duckdb duckdb Faker

cd name_generator_duckdb
python scripts/generate_names.py --rows 1000 --seed 42
python scripts/generate_products.py
python scripts/generate_sales_transactions.py --rows 5000 --seed 42

dbt deps --profiles-dir .
dbt build --profiles-dir .      # seeds + runs models + runs tests
```

Query the result:

```bash
python -c "import duckdb; print(duckdb.connect('data/name_generator.duckdb').sql('select * from customer_sales_summary order by lifetime_value desc limit 10'))"
```

## Daily automation (Windows Task Scheduler)

`scripts/daily_run.ps1` regenerates 1,000 customers + 5,000 transactions and
runs `dbt build` end to end, logging to `logs/daily_run.log`. Register it
once with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_scheduled_task.ps1 -Time 07:00
```

Manage it with `Get-ScheduledTask`, `Start-ScheduledTask`, or
`Unregister-ScheduledTask -TaskName 'NameGeneratorDbtDailyRun'`.

## dbt documentation

Every model and column is documented via YAML `description:` fields and
centralized Jinja doc blocks (`models/docs.md`), plus inline SQL comments
explaining non-obvious logic (derived columns, join types, FK relationships).

Generate and browse the interactive docs site (lineage graph, column
descriptions, test coverage) with:

```bash
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

## Note on the data

All data is synthetically generated with Faker — no real personal
information is used anywhere in this project.
