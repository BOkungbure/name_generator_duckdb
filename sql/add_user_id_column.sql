-- Migration: add a distinct user_id to the names ("customers") table.
--
-- Context: the name_generator sample data originally only had a sequential
-- integer `id` per row. To use each generated name as a "customer" that can
-- be joined against a sales_transactions table, every row needs a stable,
-- distinct user_id that is independent of row order/position.
--
-- This script is idempotent and safe to re-run against the DuckDB database
-- (data/name_generator.duckdb) if you have an existing raw_names table that
-- predates the user_id column. New data generated via
-- scripts/generate_names.py already includes user_id directly in the CSV,
-- so this script is only needed to patch an older/already-seeded table.
--
-- Run with:
--   duckdb data/name_generator.duckdb -c ".read sql/add_user_id_column.sql"

ALTER TABLE raw_names ADD COLUMN IF NOT EXISTS user_id UUID;

UPDATE raw_names
SET user_id = gen_random_uuid()
WHERE user_id IS NULL;

-- Optional: enforce uniqueness going forward.
CREATE UNIQUE INDEX IF NOT EXISTS raw_names_user_id_uq ON raw_names (user_id);
