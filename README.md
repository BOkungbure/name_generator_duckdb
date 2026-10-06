# name_generator_duckdb

A sample "name generator" dataset (fake names, emails, demographics generated
with [Faker](https://faker.readthedocs.io/)) loaded and transformed in
[DuckDB](https://duckdb.org/) using [dbt](https://www.getdbt.com/).

## Project layout

- `scripts/generate_names.py` — generates fake name records and writes them to `seeds/raw_names.csv`.
- `seeds/raw_names.csv` — the raw sample data, loaded into DuckDB via `dbt seed`.
- `models/staging/stg_names.sql` — cleaned/typed view over the raw seed.
- `models/marts/names_summary_by_state.sql` — aggregated summary table.
- `data/name_generator.duckdb` — the DuckDB database file (created on first run, git-ignored).
- `profiles.yml` — dbt connection profile pointing at the local DuckDB file.

## Setup

```bash
python -m pip install dbt-duckdb duckdb Faker
```

## Generate / refresh the sample data

```bash
python scripts/generate_names.py --rows 1000 --seed 42
```

Run with a different `--rows`/`--seed` any time to produce a new sample set.

## Load and build with dbt

All commands below use `--profiles-dir .` so dbt picks up the `profiles.yml`
in this project folder instead of `~/.dbt/profiles.yml`.

```bash
cd name_generator_duckdb

# install dbt packages (dbt_utils, if added later)
dbt deps --profiles-dir .

# load/refresh seeds/raw_names.csv into DuckDB
dbt seed --profiles-dir . --full-refresh

# build the staging + mart models
dbt run --profiles-dir .

# run the data tests (uniqueness, not_null, accepted_values)
dbt test --profiles-dir .
```

## End-to-end refresh

To regenerate a new sample set and rebuild everything in one go:

```bash
python scripts/generate_names.py --rows 1000
dbt seed --profiles-dir . --full-refresh
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Scheduling a daily refresh (Windows Task Scheduler)

Windows has no native `cron`, so the equivalent is Task Scheduler. Two scripts
automate this:

- `scripts/daily_run.ps1` — generates 1000 new names, runs `dbt seed --full-refresh`,
  then `dbt build` (run + test). Logs every step with a timestamp to `logs/daily_run.log`
  and exits non-zero on failure so Task Scheduler reports the run as failed.
- `scripts/register_scheduled_task.ps1` — registers a Windows Scheduled Task
  that runs `daily_run.ps1` every morning.

### One-time setup

```powershell
cd name_generator_duckdb
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_scheduled_task.ps1 -Time 07:00
```

This creates a task named `NameGeneratorDbtDailyRun` that runs daily at 07:00 local time.

### Managing the task

```powershell
Get-ScheduledTask -TaskName 'NameGeneratorDbtDailyRun'
Get-ScheduledTaskInfo -TaskName 'NameGeneratorDbtDailyRun'   # last run time/result, next run time
Start-ScheduledTask -TaskName 'NameGeneratorDbtDailyRun'     # trigger it manually
Unregister-ScheduledTask -TaskName 'NameGeneratorDbtDailyRun' -Confirm:$false  # remove it
```

Re-run `register_scheduled_task.ps1` with a different `-Time` to change the schedule.

## Querying the result

```bash
python -c "import duckdb; print(duckdb.connect('data/name_generator.duckdb').sql('select * from names_summary_by_state limit 10'))"
```
