"""Append one generated customer and sales batch to the Neon raw schema."""

import argparse
import csv
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

PROJECT_DIR = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_DIR / "data" / "incoming"
NAMES_FILE = BATCH_DIR / "raw_names.csv"
TRANSACTIONS_FILE = BATCH_DIR / "raw_sales_transactions.csv"

NAME_COLUMNS = (
    "source_batch_id",
    "source_row_number",
    "user_id",
    "first_name",
    "last_name",
    "full_name",
    "gender",
    "email",
    "phone_number",
    "birthdate",
    "city",
    "state",
    "country",
    "created_at",
)
TRANSACTION_COLUMNS = (
    "source_batch_id",
    "source_row_number",
    "user_id",
    "product_id",
    "order_date",
    "quantity",
    "unit_price",
    "total_amount",
    "payment_method",
    "region",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Generated input file not found: {path}")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")
        return list(reader)


def _names_rows(path: Path, batch_date: date) -> list[tuple]:
    rows = _read_csv(path)
    return [
        (
            batch_date,
            int(row["id"]),
            UUID(row["user_id"]),
            row["first_name"],
            row["last_name"],
            row["full_name"],
            row["gender"],
            row["email"],
            row["phone_number"],
            date.fromisoformat(row["birthdate"]),
            row["city"],
            row["state"],
            row["country"],
            datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def _transaction_rows(path: Path, batch_date: date) -> list[tuple]:
    rows = _read_csv(path)
    return [
        (
            batch_date,
            int(row["transaction_id"]),
            UUID(row["user_id"]),
            int(row["product_id"]),
            datetime.fromisoformat(row["order_date"]),
            int(row["quantity"]),
            Decimal(row["unit_price"]),
            Decimal(row["total_amount"]),
            row["payment_method"],
            row["region"],
        )
        for row in rows
    ]


def _connection_settings() -> dict[str, str | int]:
    required = ("NEON_HOST", "NEON_USER", "NEON_PASSWORD", "NEON_DB")
    settings: dict[str, str | int] = {}
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise EnvironmentError(
            "Missing Neon environment variable(s): " + ", ".join(missing)
        )

    settings.update(
        host=os.environ["NEON_HOST"],
        port=int(os.environ.get("NEON_PORT", "5432")),
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        dbname=os.environ["NEON_DB"],
        sslmode="require",
    )
    return settings


def _ensure_raw_tables(cursor) -> None:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.names (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source_batch_id DATE NOT NULL,
            source_row_number INTEGER NOT NULL,
            user_id UUID NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone_number TEXT NOT NULL,
            birthdate DATE NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            country TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            UNIQUE (source_batch_id, source_row_number)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.sales_transactions (
            transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source_batch_id DATE NOT NULL,
            source_row_number INTEGER NOT NULL,
            user_id UUID NOT NULL REFERENCES raw.names (user_id),
            product_id INTEGER NOT NULL,
            order_date TIMESTAMP NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
            total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
            payment_method TEXT NOT NULL,
            region TEXT NOT NULL,
            UNIQUE (source_batch_id, source_row_number)
        )
        """
    )


def load_batch(batch_date: date) -> None:
    names = _names_rows(NAMES_FILE, batch_date)
    transactions = _transaction_rows(TRANSACTIONS_FILE, batch_date)
    if not names or not transactions:
        raise ValueError("Both generated CSV files must contain at least one data row.")

    import psycopg

    with psycopg.connect(**_connection_settings()) as connection:
        with connection.cursor() as cursor:
            _ensure_raw_tables(cursor)
            cursor.execute(
                """
                SELECT
                    (SELECT count(*) FROM raw.names WHERE source_batch_id = %s),
                    (SELECT count(*) FROM raw.sales_transactions WHERE source_batch_id = %s)
                """,
                (batch_date, batch_date),
            )
            existing_names, existing_transactions = cursor.fetchone()
            if existing_names or existing_transactions:
                if (existing_names, existing_transactions) == (
                    len(names),
                    len(transactions),
                ):
                    print(
                        f"Batch {batch_date} already contains {existing_names} "
                        f"customers and {existing_transactions} transactions; skipping."
                    )
                    return
                raise RuntimeError(
                    f"Batch {batch_date} already exists with "
                    f"{existing_names} customers and {existing_transactions} "
                    f"transactions; expected {len(names)} and {len(transactions)}. "
                    "No rows were loaded."
                )

            name_placeholders = ", ".join(["%s"] * len(NAME_COLUMNS))
            transaction_placeholders = ", ".join(
                ["%s"] * len(TRANSACTION_COLUMNS)
            )
            cursor.executemany(
                f"""
                INSERT INTO raw.names ({", ".join(NAME_COLUMNS)})
                VALUES ({name_placeholders})
                ON CONFLICT (source_batch_id, source_row_number) DO NOTHING
                """,
                names,
            )
            cursor.executemany(
                f"""
                INSERT INTO raw.sales_transactions ({", ".join(TRANSACTION_COLUMNS)})
                VALUES ({transaction_placeholders})
                ON CONFLICT (source_batch_id, source_row_number) DO NOTHING
                """,
                transactions,
            )

    print(
        f"Loaded batch {batch_date}: {len(names)} customers and "
        f"{len(transactions)} transactions."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-date",
        required=True,
        type=date.fromisoformat,
        help="Batch date in YYYY-MM-DD format",
    )
    args = parser.parse_args()
    load_batch(args.batch_date)


if __name__ == "__main__":
    main()
