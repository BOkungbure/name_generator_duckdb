"""
Generates a synthetic sales transactions dataset modeled loosely on the
Microsoft "Wide World Importers" sample (stock items, orders, customers) and
writes it to data/incoming/raw_sales_transactions.csv for appending to Neon
with scripts/load_to_neon.py.

Each transaction references:
- a user_id pulled from data/incoming/raw_names.csv, so every generated name
  can be treated as a customer with purchase history.
- a product_id pulled from seeds/raw_products.csv (the product catalog), so
  product name/category/price live in one place instead of being repeated
  on every transaction row.

Usage:
    python scripts/generate_sales_transactions.py [--rows 5000] [--seed 42] [--batch-date YYYY-MM-DD]

The transaction_id CSV field is the row number within this batch. The Neon
loader stores it as source_row_number and lets Postgres assign transaction_id.
Requires the matching batch in data/incoming/raw_names.csv and the static
product catalog in seeds/raw_products.csv to exist.
"""
import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

PROJECT_DIR = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_DIR / "data" / "incoming"
SEEDS_DIR = PROJECT_DIR / "seeds"
NAMES_FILE = BATCH_DIR / "raw_names.csv"
PRODUCTS_FILE = SEEDS_DIR / "raw_products.csv"
OUTPUT_FILE = BATCH_DIR / "raw_sales_transactions.csv"

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash"]

REGIONS = [
    "North America",
    "South America",
    "Europe",
    "Asia Pacific",
    "Middle East",
    "Africa",
]


def load_user_ids() -> list[str]:
    if not NAMES_FILE.exists():
        raise SystemExit(
            f"{NAMES_FILE} not found. Run scripts/generate_names.py first."
        )
    with NAMES_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["user_id"] for row in reader]


def load_products() -> list[dict]:
    if not PRODUCTS_FILE.exists():
        raise SystemExit(
            f"{PRODUCTS_FILE} not found. Run scripts/generate_products.py first."
        )
    with PRODUCTS_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_rows(
    num_rows: int,
    seed: int,
    user_ids: list[str],
    products: list[dict],
    batch_date=None,
) -> list[dict]:
    if batch_date is None:
        batch_date = date.today()

    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)
    batch_end = datetime.combine(batch_date, datetime.max.time())
    batch_start = batch_end - timedelta(days=365)

    rows = []
    for row_id in range(1, num_rows + 1):
        product = random.choice(products)
        unit_price = float(product["unit_price"])
        quantity = random.randint(1, 10)
        total_amount = round(unit_price * quantity, 2)
        rows.append(
            {
                # The loader maps this batch-local row number to its idempotency key.
                "transaction_id": row_id,
                "user_id": random.choice(user_ids),
                "product_id": product["product_id"],
                "order_date": fake.date_time_between(
                    start_date=batch_start, end_date=batch_end
                ).isoformat(sep=" "),
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "payment_method": random.choice(PAYMENT_METHODS),
                "region": random.choice(REGIONS),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=5000, help="Number of transactions to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--batch-date",
        type=date.fromisoformat,
        default=date.today(),
        help="Batch date in YYYY-MM-DD format (defaults to today)",
    )
    args = parser.parse_args()

    user_ids = load_user_ids()
    products = load_products()

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(
        args.rows, args.seed, user_ids, products, args.batch_date
    )

    fieldnames = list(rows[0].keys())
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
