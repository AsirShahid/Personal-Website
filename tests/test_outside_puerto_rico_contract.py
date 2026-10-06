import json
import re
import unittest
from pathlib import Path

from test_outside_scout_contract import route_source

ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
PAGE_PATH = ROOT / "src/pages/outside.astro"
PR_ID = "puerto-rico-2025-june-photos"
OLD_ID = "puerto-rico-2025-june"
OLD_CANONICAL_ID = "puerto-rico-2025-june-gallery"
PR_BASELINE = json.loads((ROOT / "tests/fixtures/outside-puerto-rico-prechange-routes.json").read_text())
PR_REMOVALS = set(PR_BASELINE["removed_sources"])
PR_PREFIX = "/outside/assets/owner-review/core-trips/C"


class PuertoRicoOwnerReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}

    def test_exact_25_current_copies_and_frozen_46_ordinal_routes(self):
        self.assertEqual((len(self.studies), sum(len(s["images"]) for s in self.studies.values())), (21, 414))
        self.assertIn(PR_ID, self.studies)
        self.assertNotIn(OLD_CANONICAL_ID, self.studies)
        pr = self.studies[PR_ID]
        refs = [image["src"].rsplit("/", 1)[-1] for image in pr["images"]]
        self.assertEqual(refs, PR_BASELINE["kept_refs"])
        self.assertEqual(len(refs), 25)
        self.assertEqual(pr["status"], "PENDING")
        self.assertEqual((pr["date"], pr["dateEnd"]), ("2025-06-21", "2025-06-23"))
        self.assertEqual({day: sum(image.get("d") == day for image in pr["images"]) for day in ("2025-06-21", "2025-06-22", "2025-06-23")},
                         {"2025-06-21": 5, "2025-06-22": 17, "2025-06-23": 3})
        self.assertEqual([image["src"] for image in pr["images"]],
                         [source for source in PR_BASELINE["prechange_sources"] if source not in PR_REMOVALS])
        next_image = 0
        for display_number, series in enumerate(sorted(pr["series"], key=lambda row: row["start"]), 1):
            with self.subTest(series=display_number):
                self.assertEqual(series["displayNumber"], display_number)
                self.assertEqual(series["start"], next_image)
                images = pr["images"][series["start"]:series["start"] + series["count"]]
                self.assertGreater(len(images), 0)
                self.assertEqual(len(images), series["count"])
                self.assertTrue(all((image.get("d"), image.get("place"), image.get("transit")) ==
                                    (images[0].get("d"), images[0].get("place"), images[0].get("transit"))
                                    for image in images))
                self.assertEqual(series["date"], images[0]["d"])
                self.assertEqual(series["dateEnd"], images[-1]["d"])
                self.assertTrue(all(image["se"] == display_number for image in images))
                next_image += series["count"]
        self.assertEqual(next_image, len(pr["images"]))
        for row in PR_BASELINE["routes"]:
            expected = None if row["source"] in PR_REMOVALS else row["source"]
            self.assertEqual(route_source(self.data, row["hash"]), expected, row["hash"])
        for ref in ("C887", "C894"):
            self.assertIn(f"/outside/assets/owner-review/core-trips/{ref}", [image["src"] for image in pr["images"]])
        aliases = self.data["aliases"]
        gallery = aliases[OLD_CANONICAL_ID]
        self.assertEqual(len(gallery["targets"]), 46)
        self.assertEqual(route_source(self.data, f"#{OLD_CANONICAL_ID}"), PR_BASELINE["prechange_sources"][0])
        for alias_id in (OLD_ID, "metadata-puerto-rico-june-2025"):
            self.assertEqual([route_source(self.data, f"#{alias_id}/{i}") for i in (1, 2)],
                             ["/outside/assets/owner-review/core-trips/C887", "/outside/assets/owner-review/core-trips/C894"])

    def test_owner_hidden_studies_are_excluded_from_the_recent_worklist_only(self):
        page = PAGE_PATH.read_text()

        def listed_ids(field: str) -> list:
            match = re.search(rf"{field}:\s*\[([^]]*)\]", page)
            return re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)) if match else []

        exclude_ids = listed_ids("excludeStudyIds")
        self.assertEqual(exclude_ids, ["puerto-rico-2025-june-photos", "puerto-rico-2025-october", "georgia-2025-october"])
        include_ids = listed_ids("includeStudyIds")
        self.assertEqual(include_ids, [PR_ID])
        visible = [study for study in self.data["studies"]
                   if study["id"] not in exclude_ids
                   and (study["id"] in include_ids or (study.get("date") and study["date"] >= "2025-10-01"))]
        self.assertEqual((len(visible), sum(len(study["images"]) for study in visible)), (6, 233))
        # Hiding is display-level: every hidden study keeps its own records, routes and photos.
        for study_id, photos in (("puerto-rico-2025-june-photos", 25), ("puerto-rico-2025-october", 4), ("georgia-2025-october", 1)):
            self.assertEqual(len(self.studies[study_id]["images"]), photos)


if __name__ == "__main__":
    unittest.main()
