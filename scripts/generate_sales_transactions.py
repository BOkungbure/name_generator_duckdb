"""
Generates a synthetic sales transactions dataset modeled loosely on the
Microsoft "Wide World Importers" sample (stock items, orders, customers) and
writes it to seeds/raw_sales_transactions.csv so it can be loaded into
DuckDB with `dbt seed`.

Each transaction references:
- a user_id pulled from seeds/raw_names.csv, so every generated name can be
  treated as a customer with purchase history.
- a product_id pulled from seeds/raw_products.csv (the product catalog), so
  product name/category/price live in one place instead of being repeated
  on every transaction row.

Usage:
    python scripts/generate_sales_transactions.py [--rows 5000] [--seed 42]

Requires seeds/raw_names.csv and seeds/raw_products.csv to already exist
(run generate_names.py and generate_products.py first).
"""
import argparse
import csv
import random
from pathlib import Path

from faker import Faker

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
NAMES_FILE = SEEDS_DIR / "raw_names.csv"
PRODUCTS_FILE = SEEDS_DIR / "raw_products.csv"
OUTPUT_FILE = SEEDS_DIR / "raw_sales_transactions.csv"

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
    num_rows: int, seed: int, user_ids: list[str], products: list[dict]
) -> list[dict]:
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    rows = []
    for row_id in range(1, num_rows + 1):
        product = random.choice(products)
        unit_price = float(product["unit_price"])
        quantity = random.randint(1, 10)
        total_amount = round(unit_price * quantity, 2)
        rows.append(
            {
                "transaction_id": row_id,
                "user_id": random.choice(user_ids),
                "product_id": product["product_id"],
                "order_date": fake.date_time_between(start_date="-1y").isoformat(sep=" "),
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
    args = parser.parse_args()

    user_ids = load_user_ids()
    products = load_products()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(args.rows, args.seed, user_ids, products)

    fieldnames = list(rows[0].keys())
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
