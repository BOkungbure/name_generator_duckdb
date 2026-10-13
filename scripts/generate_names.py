"""
Generates a sample "name generator" dataset using Faker and writes it to
data/incoming/raw_names.csv for appending to Neon with scripts/load_to_neon.py.

Usage:
    python scripts/generate_names.py [--rows 1000] [--seed 42] [--batch-date YYYY-MM-DD]

The daily job derives the seed from the batch date, so a retry regenerates
the same batch while a later date generates distinct customer IDs.
"""
import argparse
import csv
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

PROJECT_DIR = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_DIR / "data" / "incoming"
OUTPUT_FILE = BATCH_DIR / "raw_names.csv"

GENDERS = ["female", "male"]


def generate_rows(num_rows: int, seed: int, batch_date=None) -> list[dict]:
    if batch_date is None:
        batch_date = date.today()

    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)
    batch_end = datetime.combine(batch_date, datetime.max.time())
    batch_start = batch_end - timedelta(days=730)
    earliest_birthdate = _years_before(batch_date, 90)
    latest_birthdate = _years_before(batch_date, 18)

    rows = []
    for row_id in range(1, num_rows + 1):
        gender = random.choice(GENDERS)
        first_name = fake.first_name_female() if gender == "female" else fake.first_name_male()
        last_name = fake.last_name()
        generated_email = fake.unique.email()
        local_part, domain = generated_email.rsplit("@", 1)
        # Deterministic (seeded) UUID so the same --seed always reproduces the
        # same user_id values for an idempotent batch retry.
        user_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
        birthdate = earliest_birthdate + timedelta(
            days=random.randint(0, (latest_birthdate - earliest_birthdate).days)
        )
        rows.append(
            {
                "id": row_id,
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "gender": gender,
                "email": f"{local_part}.{batch_date:%Y%m%d}@{domain}",
                "phone_number": fake.phone_number(),
                "birthdate": birthdate.isoformat(),
                "city": fake.city(),
                "state": fake.state(),
                "country": fake.current_country(),
                "created_at": fake.date_time_between(
                    start_date=batch_start, end_date=batch_end
                ).isoformat(sep=" "),
            }
        )
    return rows


def _years_before(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, month=2, day=28)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1000, help="Number of name records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--batch-date",
        type=date.fromisoformat,
        default=date.today(),
        help="Batch date in YYYY-MM-DD format (defaults to today)",
    )
    args = parser.parse_args()

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(args.rows, args.seed, args.batch_date)

    fieldnames = list(rows[0].keys())
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
