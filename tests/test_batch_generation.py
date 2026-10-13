import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from generate_names import generate_rows
from generate_sales_transactions import generate_rows as generate_sales_rows
from load_to_neon import _names_rows, _transaction_rows


class BatchGenerationTests(unittest.TestCase):
    def test_customer_batch_ids_and_emails_are_date_scoped(self):
        batch_date = date(2026, 10, 12)
        rows = generate_rows(5, 20261012, batch_date)

        self.assertEqual([row["id"] for row in rows], [1, 2, 3, 4, 5])
        self.assertEqual(len({row["user_id"] for row in rows}), 5)
        self.assertTrue(all(".20261012@" in row["email"] for row in rows))

    def test_customer_ids_repeat_for_same_seed(self):
        batch_date = date(2026, 10, 12)
        first = generate_rows(5, 20261012, batch_date)
        retry = generate_rows(5, 20261012, batch_date)

        self.assertEqual(
            first,
            retry,
        )

    def test_later_daily_batch_has_distinct_customer_ids(self):
        first_date = date(2026, 10, 12)
        next_date = date(2026, 10, 13)
        first_ids = {
            row["user_id"] for row in generate_rows(5, 20261012, first_date)
        }
        next_ids = {
            row["user_id"] for row in generate_rows(5, 20261013, next_date)
        }

        self.assertTrue(first_ids.isdisjoint(next_ids))

    def test_sales_rows_are_reproducible_for_a_batch_date(self):
        batch_date = date(2026, 10, 12)
        customers = ["3eb13b90-4668-4257-bdd6-40fb06671ad1"]
        products = [
            {
                "product_id": "1",
                "product_name": "Sample item",
                "category": "Sample",
                "unit_price": "8.50",
            }
        ]

        first = generate_sales_rows(5, 20261012, customers, products, batch_date)
        retry = generate_sales_rows(5, 20261012, customers, products, batch_date)

        self.assertEqual(first, retry)

    def test_loader_maps_batch_row_ids_to_source_row_numbers(self):
        batch_date = date(2026, 10, 12)
        names_csv = (
            "id,user_id,first_name,last_name,full_name,gender,email,phone_number,"
            "birthdate,city,state,country,created_at\n"
            "1,3eb13b90-4668-4257-bdd6-40fb06671ad1,A,B,A B,female,"
            "a.20261012@example.net,555-0100,2000-01-02,City,State,Country,"
            "2026-10-01 12:00:00\n"
        )
        transactions_csv = (
            "transaction_id,user_id,product_id,order_date,quantity,unit_price,"
            "total_amount,payment_method,region\n"
            "1,3eb13b90-4668-4257-bdd6-40fb06671ad1,1,"
            "2026-10-02 12:00:00,2,8.50,17.00,credit_card,Europe\n"
        )

        with tempfile.TemporaryDirectory() as directory:
            names_path = Path(directory) / "names.csv"
            transactions_path = Path(directory) / "transactions.csv"
            names_path.write_text(names_csv, encoding="utf-8")
            transactions_path.write_text(transactions_csv, encoding="utf-8")

            name_row = _names_rows(names_path, batch_date)[0]
            transaction_row = _transaction_rows(
                transactions_path, batch_date
            )[0]

        self.assertEqual(name_row[0:2], (batch_date, 1))
        self.assertEqual(transaction_row[0:2], (batch_date, 1))
        self.assertEqual(
            transaction_row[6:8], (Decimal("8.50"), Decimal("17.00"))
        )


if __name__ == "__main__":
    unittest.main()
