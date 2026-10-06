"""
Generates a synthetic sales transactions dataset modeled loosely on the
Microsoft "Wide World Importers" sample (stock items, orders, customers) and
writes it to seeds/raw_sales_transactions.csv so it can be loaded into
DuckDB with `dbt seed`.

Each transaction references a user_id pulled from seeds/raw_names.csv, so
every generated name can be treated as a customer with purchase history.

Usage:
    python scripts/generate_sales_transactions.py [--rows 5000] [--seed 42]

Requires seeds/raw_names.csv to already exist (run generate_names.py first).
"""
import argparse
import csv
import random
from pathlib import Path

from faker import Faker

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
NAMES_FILE = SEEDS_DIR / "raw_names.csv"
OUTPUT_FILE = SEEDS_DIR / "raw_sales_transactions.csv"

# A small stand-in "stock item" catalog in the spirit of Wide World
# Importers' novelty/gift items, since the real WWI database is a SQL
# Server sample (not a flat file) and isn't pulled in here.
PRODUCT_CATALOG = [
    ("Novelty Chilli Chocolates 250g", "Confectionery", 8.50),
    ("USB Food Flash Drive - Chocolate", "Novelty Items", 12.00),
    ("Ride On Dinosaur Costume", "Costumes", 145.00),
    ("Air Cushion Machine", "Packaging", 1850.00),
    ("Alien Egg Fidget Ball", "Novelty Items", 6.25),
    ("Developer Flashing Fish Hat", "Novelty Items", 18.75),
    ("Clear Ethernet Cable 2m", "Electronics", 9.99),
    ("Ergonomic Keyboard", "Electronics", 65.00),
    ("Packaging Tape Dispenser", "Packaging", 22.50),
    ("Magic Flashing Fruit Bowl", "Novelty Items", 34.00),
    ("Giant Chocolate Snake 1.2m", "Confectionery", 45.00),
    ("50mm Double Sided Tape", "Packaging", 5.75),
    ("Furry Gloves (Black) S", "Clothing", 15.50),
    ("Superhero Mask (Red)", "Costumes", 11.25),
    ("RC Mini Monster Truck", "Toys", 28.00),
]

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


def generate_rows(num_rows: int, seed: int, user_ids: list[str]) -> list[dict]:
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    rows = []
    for row_id in range(1, num_rows + 1):
        product_name, category, unit_price = random.choice(PRODUCT_CATALOG)
        quantity = random.randint(1, 10)
        total_amount = round(unit_price * quantity, 2)
        rows.append(
            {
                "transaction_id": row_id,
                "user_id": random.choice(user_ids),
                "order_date": fake.date_time_between(start_date="-1y").isoformat(sep=" "),
                "product_name": product_name,
                "category": category,
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

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(args.rows, args.seed, user_ids)

    fieldnames = list(rows[0].keys())
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
