import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
FROZEN = json.loads((ROOT / "tests/fixtures/outside-pr45-source-route-baseline.json").read_text())
RESTORED_SOURCE = FROZEN["authorized_restore_source"]["src"]
REMOVED_SOURCES = set(FROZEN["pending_removal_sources"])


def route_source(data, route_hash):
    match = re.fullmatch(r"#([\w-]+)(?:/([1-9]\d*))?", route_hash)
    if not match:
        return None
    route_id, ordinal = match.groups()
    study = next((item for item in data["studies"] if item["id"] == route_id), None)
    if study is not None:
        index = min(int(ordinal) - 1, len(study["images"]) - 1) if ordinal else 0
        return study["images"][index]["src"] if study["images"] else None
    alias = data["aliases"].get(route_id)
    if alias is None:
        return None
    if "targets" in alias:
        target = alias.get("defaultTarget") if ordinal is None else (
            alias["targets"][int(ordinal) - 1] if int(ordinal) <= len(alias["targets"]) else None
        )
        if not target:
            return None
        target_study = next((item for item in data["studies"] if item["id"] == target.get("studyId")), None)
        index = target.get("index")
        return target_study["images"][index]["src"] if target_study and isinstance(index, int) and 0 <= index < len(target_study["images"]) else None
    target_study = next((item for item in data["studies"] if item["id"] == alias.get("studyId")), None)
    if ordinal is None:
        index = alias.get("defaultIndex", -1)
    else:
        indices = alias.get("indices", [])
        index = indices[int(ordinal) - 1] if int(ordinal) <= len(indices) else None
    return target_study["images"][index]["src"] if target_study and isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(target_study["images"]) else None


class OutsideScoutAndRemovalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}
        cls.images = {image["src"]: image for study in cls.data["studies"] for image in study["images"]}

    def test_final_owner_inventory_and_all_source_keyed_removals(self):
        expected = FROZEN["expected_inventory"]
        self.assertEqual((len(self.studies), len(self.images)), (expected["studies"], expected["photos"]))
        baseline_sources = set(FROZEN["image_object_sha256"])
        self.assertEqual(set(self.images), (baseline_sources - REMOVED_SOURCES) | {RESTORED_SOURCE})
        self.assertEqual(len(REMOVED_SOURCES), 16)
        for source in REMOVED_SOURCES | set(FROZEN["effective_excluded_sources"]):
            if source != RESTORED_SOURCE:
                self.assertNotIn(source, self.images, source)
        self.assertEqual(len(FROZEN["effective_excluded_sources"]), expected["effective_exclusions"])
        self.assertNotIn(RESTORED_SOURCE, FROZEN["effective_excluded_sources"])
        for source, digest in FROZEN["image_object_sha256"].items():
            if source in self.images:
                actual = hashlib.sha256(json.dumps(self.images[source], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                self.assertEqual(actual, digest, source)
        self.assertEqual(self.images[RESTORED_SOURCE], FROZEN["authorized_restore_source"])
        order = [study["id"] for study in self.data["studies"]]
        self.assertEqual(order[:3], ["new-zealand-2026-july-photos", "australia-2026-july-gallery", "pakistan-2026-summer-gallery"])
        self.assertNotIn("baseball-stadium-2023-may", self.studies)

    def test_scout_series_are_zero_presentation_only_and_keep_destination_series(self):
        for spec in FROZEN["scout_contract"]:
            with self.subTest(study=spec["study_id"]):
                study = self.studies[spec["canonical_id"]]
                self.assertEqual((study["date"], study["dateEnd"]), tuple(spec["study_dates"]))
                scout = study["series"][0]
                self.assertEqual(scout.get("displayNumber"), 0)
                self.assertEqual(scout["title"], spec["series_title"])
                self.assertEqual((scout["date"], scout["dateEnd"]), tuple(spec["dates"]))
                self.assertEqual((scout["start"], scout["count"], scout["key"]), (0, len(spec["sources"]), 0))
                self.assertEqual([image["src"] for image in study["images"][:len(spec["sources"])]], spec["sources"])
                existing = study["series"][1:]
                self.assertEqual([series.get("displayNumber") for series in existing], spec["destination_displays"])
                self.assertEqual([series["start"] for series in study["series"]], sorted(series["start"] for series in study["series"]))
        pakistan = self.studies["pakistan-2026-summer-gallery"]
        australia = self.studies["australia-2026-july-gallery"]
        cruise = self.studies["cruise-2024-december-gallery"]
        self.assertEqual((len(pakistan["images"]), len(pakistan["series"])), (32, 7))
        self.assertEqual((len(australia["images"]), len(australia["series"])), (36, 8))
        self.assertEqual((len(cruise["images"]), len(cruise["series"])), (8, 6))
        self.assertEqual(pakistan["date"], "2026-06-28")
        self.assertEqual((australia["date"], australia["dateEnd"]), ("2026-07-07", "2026-07-16"))
        self.assertEqual((cruise["date"], cruise["dateEnd"]), ("2024-12-15", "2024-12-20"))

    def test_corrected_public_labels_use_new_canonical_ids_and_old_source_aliases(self):
        for correction in FROZEN["label_corrections"]:
            with self.subTest(old_id=correction["old_study_id"]):
                study = self.studies[correction["suggested_unused_canonical_id"]]
                self.assertEqual((study["place"], study["region"], study["country"]), (correction["place"], correction["region"], correction["country"]))
                self.assertEqual([image["src"] for image in study["images"]], correction["sources"])
                if correction["series_title"]:
                    self.assertEqual([series["title"] for series in study["series"]], [correction["series_title"]])
                self.assertIn(correction["old_study_id"], self.data["aliases"])
                old = self.data["aliases"][correction["old_study_id"]]
                self.assertTrue(old.get("targets"))
                self.assertEqual([route_source(self.data, f"#{correction['old_study_id']}/{i}") for i in range(1, len(correction["sources"]) + 1)], correction["sources"])

    def test_all_2305_frozen_routes_keep_the_same_source_except_approved_unavailability_and_restore(self):
        routes = FROZEN["routes"]
        self.assertEqual(len(routes), 2305)
        self.assertEqual(len({row["hash"] for row in routes}), len(routes))
        allowed_restore = set(FROZEN["allowed_restored_routes"])
        actual_restored = {row["hash"] for row in routes if row["source"] is None and route_source(self.data, row["hash"]) == RESTORED_SOURCE}
        self.assertEqual(actual_restored, allowed_restore)
        for row in routes:
            with self.subTest(route=row["hash"]):
                expected = RESTORED_SOURCE if row["hash"] in allowed_restore else (None if row["source"] in REMOVED_SOURCES else row["source"])
                self.assertEqual(route_source(self.data, row["hash"]), expected, row["hash"])


if __name__ == "__main__":
    unittest.main()
