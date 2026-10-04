import json
import re
import unittest
from pathlib import Path

DATA = Path(__file__).parents[1] / "src/data/outside-studies.json"
OWNER_REMOVALS = {
    "/outside/assets/owner-review/core-trips/C538",
    "/outside/assets/owner-review/core-trips/C542",
    "/outside/assets/owner-review/core-trips/C941",
    "/outside/hoover-dam/005",
    "/outside/study-0726/006",
}


class OutsideContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}
        cls.sources = {image["src"] for study in cls.data["studies"] for image in study["images"]}

    def test_final_inventory_and_readable_non_reused_canonical_ids(self):
        ids = set(self.studies)
        self.assertEqual((len(ids), sum(len(s["images"]) for s in self.studies.values())), (28, 511))
        for study_id in ids:
            self.assertRegex(study_id, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertFalse(re.search(r"projection|metadata|retained|expanded|review|candidate|supplement", study_id), study_id)
        self.assertFalse(ids & set(self.data["aliases"]))
        self.assertFalse(self.sources & OWNER_REMOVALS)
        self.assertEqual(len(self.data["aliases"]), 89)

    def test_public_copy_is_clean_and_genuine_uncertainty_is_preserved(self):
        forbidden = re.compile(r"archived state label|metadata (?:review|cluster)|unsorted review|review supplement|location pending", re.I)
        for study in self.data["studies"]:
            public = " ".join([study.get("place", ""), study.get("region", ""), study.get("country", "")])
            self.assertIsNone(forbidden.search(public), f"{study['id']}: {public}")
        self.assertEqual(self.studies["thailand-2026-july"]["status"], "PENDING")
        self.assertEqual(self.studies["thailand-2026-july"]["region"], "Location unconfirmed")
        self.assertEqual(self.studies["celebration-2025-september"]["status"], "PENDING")
        self.assertEqual(self.studies["marlborough-2025-may"]["status"], "PENDING")
        self.assertEqual(self.studies["cruise-2024-december"]["status"], "PENDING")
        self.assertEqual(self.studies["august-2023-photos"]["place"], "Location unconfirmed")

    def test_mixed_year_catch_all_is_split_by_capture_date_with_old_routes_bound(self):
        expected = {
            "baseball-stadium-2023-may": ("2023-05-14", 1),
            "resort-scenes-2025-june": ("2025-06-14", 4),
            "aquarium-scenes-2025-june": ("2025-06-18", 18),
        }
        for study_id, (date, count) in expected.items():
            study = self.studies[study_id]
            self.assertEqual((study["date"], study["dateEnd"], len(study["images"])), (date, date, count))
            self.assertEqual(study["status"], "PENDING")
            self.assertTrue(all(image["d"] == date for image in study["images"]))
        alias = self.data["aliases"]["unsorted-review"]
        self.assertEqual(len(alias["targets"]), 23)
        self.assertEqual(alias["defaultTarget"], {"studyId": "baseball-stadium-2023-may", "index": 0})
        self.assertEqual(alias["targets"][0], {"studyId": "baseball-stadium-2023-may", "index": 0})
        self.assertEqual(alias["targets"][1], {"studyId": "resort-scenes-2025-june", "index": 0})
        self.assertEqual(alias["targets"][5], {"studyId": "aquarium-scenes-2025-june", "index": 0})

    def test_series_titles_are_concise_scene_labels_not_dates_or_workflow_copy(self):
        date_title = re.compile(r"^\d{4}-\d{2}-\d{2}$|^[A-Z][a-z]+ \d{1,2}, \d{4}$")
        for study in self.data["studies"]:
            for series in study["series"]:
                title = series.get("title", "")
                self.assertTrue(title.strip(), study["id"])
                self.assertIsNone(date_title.match(title), f"{study['id']}: {title}")
                self.assertNotIn("undefined", title.lower())
                self.assertLessEqual(len(title.split()), 5, f"{study['id']}: {title}")
                self.assertIsNone(re.search(r"metadata|review|supplement|candidate|retained", title, re.I), title)
        self.assertEqual(self.studies["australia-2026-july"]["series"][0]["title"], "Busselton Jetty")
        self.assertEqual(self.studies["thailand-2026-july"]["series"][0]["title"], "Gilded shrine & garden")
        self.assertEqual(self.studies["cruise-2024-december"]["series"][1]["title"], "Ship & open water")
        self.assertEqual(self.studies["august-2023-photos"]["series"][0]["title"], "Garden gate & paths")
        europe = self.studies["europe-shared-album"]
        self.assertEqual((europe["date"], europe["dateEnd"]), ("", ""))
        self.assertEqual(sum(not image.get("d") for image in europe["images"]), 17)
        self.assertEqual((europe["series"][0]["date"], europe["series"][1]["date"]), ("2023-02-19", ""))

    def test_worklist_uses_full_end_and_start_dates_in_descending_order(self):
        order = [s["id"] for s in self.data["studies"]]
        sorted_ids = [s["id"] for s in sorted(self.data["studies"], key=lambda s: (s.get("dateEnd") or s.get("date") or "", s.get("date") or ""), reverse=True)]
        self.assertEqual(order, sorted_ids)
        self.assertLess(order.index("august-2023-photos"), order.index("montreal-2023-august"))
        self.assertLess(order.index("montreal-2023-august"), order.index("philadelphia-2023-spring"))
        self.assertLess(order.index("albania-2026-june"), order.index("rome-vatican-2026-june"))

    def test_november_montreal_supplement_is_additive_and_has_priority_source(self):
        study = self.studies["montreal-november-2025"]
        self.assertEqual(len(study["images"]), 23)
        sources = [image["src"] for image in study["images"]]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertTrue(any("50687dc46ae34c23be92b217abb3de9f" in source for source in sources))
        self.assertEqual(sum("/montreal-november-album-gap/" in source for source in sources), 15)
        self.assertEqual([series["date"] for series in study["series"]], ["2025-11-27", "2025-11-28", "2025-11-29", "2025-11-30"])
        self.assertEqual([series["count"] for series in study["series"]], [1, 6, 15, 1])
        self.assertEqual(study["status"], "PENDING")
        self.assertEqual((study["date"], study["dateEnd"]), ("2025-11-27", "2025-11-30"))

    def test_owner_approved_utah_night_sky_photo_is_added_once_and_chronological(self):
        study = self.studies["american-southwest-2025-october"]
        photos = [i for i, image in enumerate(study["images"]) if image["src"] == "/outside/assets/utah-night-sky-2025/utah-night-sky-01"]
        self.assertEqual(len(photos), 1)
        index = photos[0]
        image = study["images"][index]
        self.assertEqual((image["d"], image["t"], image["tz"], image["alt"]), ("2025-10-12", "22:42:19", "UTC-06:00", "A field of stars against a blue night sky in Utah."))
        series_index = image["se"] - 1
        self.assertEqual(study["series"][series_index]["title"], "Utah night sky")
        self.assertEqual(study["series"][series_index]["count"], 1)
        self.assertLess(index, next(i for i, item in enumerate(study["images"]) if item["d"] == "2025-10-13"))


if __name__ == "__main__":
    unittest.main()
