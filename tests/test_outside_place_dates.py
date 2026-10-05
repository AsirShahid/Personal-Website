import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
HELPER_URL = (ROOT / "src/utils/outside-date.js").as_uri()


class OutsidePlaceDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = f'''import * as dates from {json.dumps(HELPER_URL)};
const compact = dates.formatOutsideCompactDateRange;
const legacy = dates.formatOutsideDateRange;
const cases = [
  ["2026-07-17", "2026-07-19"],
  ["2026-06-28", "2026-07-05"],
  ["2025-12-30", "2026-01-02"],
  ["2026-07-17", "2026-07-17"],
  ["2026-07-17", ""],
  ["2026-02-30", "2026-03-02"],
];
console.log(JSON.stringify({{available: typeof compact === "function", compact: compact ? cases.map(([a,b]) => compact(a,b)) : [], legacy: cases.map(([a,b]) => legacy(a,b))}}));'''
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.result = json.loads(result.stdout)

    def test_compact_ranges_distinguish_same_month_month_boundary_and_year_boundary(self):
        self.assertTrue(self.result["available"], "compact date formatter has not been implemented")
        self.assertEqual(
            self.result["compact"][:4],
            [
                "Jul 17–19, 2026",
                "Jun 28 – Jul 5, 2026",
                "Dec 30, 2025 – Jan 2, 2026",
                "Jul 17, 2026",
            ],
        )

    def test_invalid_dates_remain_literal_instead_of_being_normalized(self):
        self.assertTrue(self.result["available"], "compact date formatter has not been implemented")
        self.assertEqual(self.result["compact"][5], "2026-02-30 to 2026-03-02")

    def test_single_dates_are_compact_when_the_end_is_missing(self):
        self.assertEqual(self.result["compact"][4], "Jul 17, 2026")

    def test_legacy_date_range_formatter_remains_unchanged_for_viewer_overlay(self):
        self.assertEqual(
            self.result["legacy"],
            [
                "2026-07-17 to 07-19",
                "2026-06-28 to 07-05",
                "2025-12-30 to 2026-01-02",
                "2026-07-17",
                "2026-07-17",
                "2026-02-30 to 2026-03-02",
            ],
        )


if __name__ == "__main__":
    unittest.main()
