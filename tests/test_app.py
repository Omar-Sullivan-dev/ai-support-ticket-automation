import csv
import tempfile
import unittest
from pathlib import Path

from app import demo_analyze, load_knowledge_base, process_tickets, retrieve_context


ROOT = Path(__file__).resolve().parents[1]


class TicketAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = load_knowledge_base(ROOT / "data" / "knowledge_base.json")

    def test_retrieves_billing_article(self):
        article = retrieve_context("I was charged twice for my subscription", self.articles)
        self.assertEqual(article["id"], "KB-202")

    def test_demo_classifies_account_access(self):
        ticket = {
            "customer_name": "Test User",
            "subject": "Locked out",
            "message": "I cannot login because my password is not working.",
        }
        article = retrieve_context(ticket["subject"] + " " + ticket["message"], self.articles)
        result = demo_analyze(ticket, article)
        self.assertEqual(result["category"], "account_access")
        self.assertEqual(result["priority"], "high")

    def test_pipeline_writes_all_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "results.csv"
            count = process_tickets(
                ROOT / "data" / "sample_tickets.csv",
                output,
                ROOT / "data" / "knowledge_base.json",
            )
            with output.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(count, 4)
            self.assertEqual(len(rows), 4)
            self.assertIn("draft_response", rows[0])


if __name__ == "__main__":
    unittest.main()
