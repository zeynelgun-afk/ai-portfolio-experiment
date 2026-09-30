import csv
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReportingConsistencyTest(unittest.TestCase):
    def test_report_totals_match_the_same_day_history_row(self):
        report = (ROOT / "REPORT.md").read_text(encoding="utf-8")
        date_match = re.search(r"^# Portfolio Report — (\d{4}-\d{2}-\d{2})$", report, re.M)
        self.assertIsNotNone(date_match, "portfolio report date is missing")
        report_date = date_match.group(1)

        with (ROOT / "history.csv").open(newline="", encoding="utf-8") as handle:
            rows = {row["date"]: row for row in csv.DictReader(handle)}
        self.assertIn(report_date, rows, "report date has no matching equity-curve record")

        expected = {}
        for key, label in (("portfolio", "**AI Portfolio**"), ("spy", "SPY (100k on the same day)"),
                           ("smh", "SMH (100k on the same day)")):
            match = re.search(rf"\| {re.escape(label)} \| ([\d,]+) \$ \|", report)
            self.assertIsNotNone(match, f"{label} total is missing from report")
            expected[key] = int(match.group(1).replace(",", ""))

        row = rows[report_date]
        for key in expected:
            self.assertEqual(round(float(row[f"{key}_usd"])), expected[key],
                             f"{key} report total differs from same-day history")


if __name__ == "__main__":
    unittest.main()
