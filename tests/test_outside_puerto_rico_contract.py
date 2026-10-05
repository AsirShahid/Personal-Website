import json
import re
import unittest
from pathlib import Path

from test_outside_scout_contract import route_source

ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
PAGE_PATH = ROOT / "src/pages/outside.astro"
PR_ID = "puerto-rico-2025-june-gallery"
OLD_ID = "puerto-rico-2025-june"
PR_PREFIX = "/outside/assets/owner-review/core-trips/C"


class PuertoRicoOwnerReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}

    def test_all_46_rows_are_source_bound_and_legacy_routes_keep_their_old_photos(self):
        self.assertEqual((len(self.studies), sum(len(s["images"]) for s in self.studies.values())), (21, 485))
        self.assertIn(PR_ID, self.studies)
        self.assertNotIn(OLD_ID, self.studies)
        pr = self.studies[PR_ID]
        refs = [int(re.search(r"C(\d{3})$", image["src"]).group(1)) for image in pr["images"]]
        self.assertEqual(set(refs), set(range(877, 923)))
        self.assertEqual(len(refs), 46, "duplicate current-copy sources remain separate owner-review rows")
        self.assertEqual(pr["status"], "PENDING")
        self.assertEqual((pr["date"], pr["dateEnd"]), ("2025-06-21", "2025-06-23"))
        self.assertEqual({day: sum(image.get("d") == day for image in pr["images"]) for day in ("2025-06-21", "2025-06-22", "2025-06-23")},
                         {"2025-06-21": 10, "2025-06-22": 30, "2025-06-23": 6})
        self.assertEqual([(group["date"], group["count"]) for group in pr["series"]],
                         [("2025-06-21", 10), ("2025-06-22", 30), ("2025-06-23", 6)])
        self.assertEqual(route_source(self.data, f"#{OLD_ID}"), "/outside/assets/owner-review/core-trips/C887")
        self.assertEqual(route_source(self.data, f"#{OLD_ID}/1"), "/outside/assets/owner-review/core-trips/C887")
        self.assertEqual(route_source(self.data, f"#{OLD_ID}/2"), "/outside/assets/owner-review/core-trips/C894")
        self.assertEqual(route_source(self.data, "#metadata-puerto-rico-june-2025"),
                         "/outside/assets/owner-review/core-trips/C887")
        aliases = self.data["aliases"]
        for alias_id in (OLD_ID, "metadata-puerto-rico-june-2025"):
            alias = aliases[alias_id]
            self.assertEqual([route_source(self.data, f"#{alias_id}/{i}") for i in range(1, 3)],
                             ["/outside/assets/owner-review/core-trips/C887", "/outside/assets/owner-review/core-trips/C894"])
            self.assertEqual(alias["targets"][0]["studyId"], PR_ID)
            self.assertEqual(alias["targets"][1]["studyId"], PR_ID)

    def test_only_the_new_puerto_rico_canonical_is_the_recent_worklist_exception(self):
        page = PAGE_PATH.read_text()
        include_match = re.search(r"includeStudyIds:\s*\[([^]]*)\]", page)
        self.assertIsNotNone(include_match)
        include_ids = re.findall(r"['\"]([^'\"]+)['\"]", include_match.group(1))
        self.assertEqual(include_ids, [PR_ID])
        visible = [study for study in self.data["studies"]
                   if study["id"] in include_ids or (study.get("date") and study["date"] >= "2025-10-01")]
        self.assertEqual((len(visible), sum(len(study["images"]) for study in visible)), (9, 334))


if __name__ == "__main__":
    unittest.main()
