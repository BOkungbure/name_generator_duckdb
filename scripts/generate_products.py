"""
Generates a small synthetic product catalog, modeled loosely on the stock
items in Microsoft's "Wide World Importers" sample, and writes it to
seeds/raw_products.csv so it can be loaded into DuckDB with `dbt seed`.

This is a static reference/dimension table: it does not take --rows, since
it's meant to represent a fixed catalog of stock items rather than a stream
of randomly generated records. scripts/generate_sales_transactions.py
references product_id from this file for every transaction.

Usage:
    python scripts/generate_products.py
"""
from pathlib import Path
import csv

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
OUTPUT_FILE = SEEDS_DIR / "raw_products.csv"

# product_id, product_name, category, unit_price
PRODUCT_CATALOG = [
    (1, "Novelty Chilli Chocolates 250g", "Confectionery", 8.50),
    (2, "USB Food Flash Drive - Chocolate", "Novelty Items", 12.00),
    (3, "Ride On Dinosaur Costume", "Costumes", 145.00),
    (4, "Air Cushion Machine", "Packaging", 1850.00),
    (5, "Alien Egg Fidget Ball", "Novelty Items", 6.25),
    (6, "Developer Flashing Fish Hat", "Novelty Items", 18.75),
    (7, "Clear Ethernet Cable 2m", "Electronics", 9.99),
    (8, "Ergonomic Keyboard", "Electronics", 65.00),
    (9, "Packaging Tape Dispenser", "Packaging", 22.50),
    (10, "Magic Flashing Fruit Bowl", "Novelty Items", 34.00),
    (11, "Giant Chocolate Snake 1.2m", "Confectionery", 45.00),
    (12, "50mm Double Sided Tape", "Packaging", 5.75),
    (13, "Furry Gloves (Black) S", "Clothing", 15.50),
    (14, "Superhero Mask (Red)", "Costumes", 11.25),
    (15, "RC Mini Monster Truck", "Toys", 28.00),
]


def main() -> None:
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_name", "category", "unit_price"])
        writer.writerows(PRODUCT_CATALOG)

    print(f"Wrote {len(PRODUCT_CATALOG)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
