# Name Generator → Sales Analytics (dbt + Neon)

This portfolio project demonstrates an analytics engineering pipeline with
Python/Faker, append-only ingestion into Neon Postgres, and tested dbt staging
and mart models.

## Architecture

```text
Python/Faker ──► batch CSVs ──► Python loader ──► Neon raw schema
                                                   │
                                      dbt sources + product seed
                                                   │
                                     staging views → marts
```

Customer and transaction batches are appended to Neon by
`scripts/load_to_neon.py`; they are not dbt seeds. A batch date and source row
number make the load safe to retry. Neon assigns persistent customer and
transaction surrogate IDs. The small, version-controlled product catalog
remains a dbt seed, which is an appropriate use of seeds for static reference
data.

## Project layout

| Path | Purpose |
|---|---|
| `scripts/generate_names.py` | Generates a deterministic customer batch with unique UUIDs |
| `scripts/generate_products.py` | Rebuilds the small static product catalog CSV |
| `scripts/generate_sales_transactions.py` | Generates transactions referencing the current customer batch and product catalog |
| `scripts/load_to_neon.py` | Creates raw tables when needed and appends a batch transactionally |
| `seeds/raw_products.csv` | Static product reference data loaded by `dbt seed` |
| `data/incoming/raw_names.csv`, `data/incoming/raw_sales_transactions.csv` | Temporary generated batch files (also used for the initial import) |
| `models/sources.yml` | Declares the Neon raw tables as dbt sources |
| `models/staging/` | Cleaned views over raw Neon sources and the product seed |
| `models/marts/` | Customer-sales join and summary tables |
| `snapshots/product_catalog_snapshot.sql` | Preserves product catalog history when its name, category, or price changes |
| `scripts/daily_run.ps1` | Daily generation, append, seed, dbt build, and logging |
| `scripts/register_scheduled_task.ps1` | Registers the Windows Task Scheduler job |
| `profiles.yml` | dbt Postgres profile; credentials are read from environment variables |

## Install and configure

Install dependencies in the Python environment used by the scheduled task:

```powershell
python -m pip install -r requirements.txt
```

Set `NEON_HOST`, `NEON_PORT` (optional; defaults to `5432`), `NEON_USER`,
`NEON_PASSWORD`, and `NEON_DB` in the Windows account environment used to run
dbt and Task Scheduler. `profiles.yml` requires SSL and does not contain
credentials. Never commit a Neon connection string or password.

The local `profiles.yml` is ignored by Git. Create it from the safe template:

```powershell
Copy-Item .\profiles.example.yml .\profiles.yml
```

Check the profile and connection:

```powershell
dbt debug --profiles-dir .
```

## Initial load

Load the current generated CSV snapshot once **before** registering or running
the scheduled job. The checked-in files are moved out of dbt's `seeds/`
directory to `data/incoming/`; this preserves the existing sample data for
the initial import and keeps generated batches out of dbt's seed inventory:

```powershell
dbt seed --select raw_products --profiles-dir .
$BatchDate = Get-Date -Format "yyyy-MM-dd"
python .\scripts\load_to_neon.py --batch-date $BatchDate
dbt snapshot --select product_catalog_snapshot --profiles-dir .
dbt build --exclude resource_type:seed --profiles-dir .
```

The first snapshot run records the current catalog as its baseline. Subsequent
runs create a new version when `product_name`, `category`, or `unit_price`
changes. Snapshot history is stored in the `analytics_snapshots` schema.

The loader creates `raw.names` and `raw.sales_transactions` if they do not
already exist. It inserts customers before their sales, within one database
transaction, and enforces uniqueness and a customer foreign key. Running the
same batch date again with the same row counts skips the batch; mismatched
counts fail instead of silently mixing regenerated rows with previously
loaded data.

## Daily automation

The scheduled job generates 1,000 customers and 5,000 sales transactions.
Its date-derived random seed makes same-day retries reproducible; later days
produce distinct customer UUIDs. It appends the batch, refreshes the small
product seed, snapshots catalog changes, then runs dbt models and tests
(excluding seeds from the build).
The run log is `logs/daily_run.log`.

Register the task:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_scheduled_task.ps1 -Time 07:00
```

The scheduled task must run as the Windows account whose environment contains
the Neon variables and which has the project dependencies installed. Manage it
with `Get-ScheduledTask`, `Start-ScheduledTask`, or
`Unregister-ScheduledTask -TaskName 'NameGeneratorDbtDailyRun'`.

## dbt docs and tests

Model and column descriptions are defined in YAML and centralized Jinja docs
in `models/docs.md`. Run the models and tests with:

```powershell
dbt build --exclude resource_type:seed --profiles-dir .
```

Regenerate/browse dbt documentation with:

```powershell
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

All customer and transaction data is synthetic; no real personal information
is used in this project.
