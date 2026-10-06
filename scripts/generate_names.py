"""
Generates a sample "name generator" dataset using Faker and writes it to
seeds/raw_names.csv so it can be loaded into DuckDB with `dbt seed`.

Usage:
    python scripts/generate_names.py [--rows 1000] [--seed 42]

Re-run this (optionally with a different --seed) and then `dbt seed --full-refresh`
to refresh/update the sample data.
"""
import argparse
import csv
import random
import uuid
from pathlib import Path

from faker import Faker

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
OUTPUT_FILE = SEEDS_DIR / "raw_names.csv"

GENDERS = ["female", "male"]


def generate_rows(num_rows: int, seed: int) -> list[dict]:
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    rows = []
    for row_id in range(1, num_rows + 1):
        gender = random.choice(GENDERS)
        first_name = fake.first_name_female() if gender == "female" else fake.first_name_male()
        last_name = fake.last_name()
        # Deterministic (seeded) UUID so the same --seed always reproduces the
        # same user_id values; used as the stable customer key joined against
        # the sales_transactions table.
        user_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
        rows.append(
            {
                "id": row_id,
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "gender": gender,
                "email": fake.unique.email(),
                "phone_number": fake.phone_number(),
                "birthdate": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
                "city": fake.city(),
                "state": fake.state(),
                "country": fake.current_country(),
                "created_at": fake.date_time_between(start_date="-2y").isoformat(sep=" "),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1000, help="Number of name records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(args.rows, args.seed)

    fieldnames = list(rows[0].keys())
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
