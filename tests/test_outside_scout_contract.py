import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
LEGACY_BASELINE_REV = "f89fb3b"
FROZEN = json.loads((ROOT / "tests/fixtures/outside-pr45-source-route-baseline.json").read_text())
OWNER_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005.json").read_text())
LATEST_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005-161007.json").read_text())
OWNER_EXPORT_REMOVALS = set(OWNER_FLAGS["flagged_sources"]) | set(LATEST_FLAGS["flagged_sources"])
RESTORED_SOURCE = FROZEN["authorized_restore_source"]["src"]
REMOVED_SOURCES = set(FROZEN["pending_removal_sources"])
NEW_REMOVALS = {
    "/outside/assets/owner-review/core-trips/C066",
    "/outside/assets/owner-review/core-trips/C104",
    "/outside/assets/owner-review/core-trips/C107",
    "/outside/assets/owner-review/core-trips/C115",
    "/outside/assets/owner-review/core-trips/C175",
    "/outside/assets/owner-review/core-trips/C256",
    "/outside/assets/owner-review/core-trips/C308",
    "/outside/assets/owner-review/core-trips/C321",
    "/outside/assets/owner-review/core-trips/C430",
}
DUPLICATE_REMOVALS = {
    "/outside/assets/owner-review/galapagos/G208",
    "/outside/assets/owner-review/core-trips/C219",
    "/outside/assets/owner-review/core-trips/C351",
    "/outside/assets/owner-review/core-trips/C484",
    "/outside/assets/owner-review/additional-trips/A460",
    "/outside/assets/owner-review/additional-trips/A508",
    "/outside/assets/owner-review/additional-trips/A505",
    "/outside/assets/owner-review/additional-trips/A514",
}
PARENT_ROUTES = json.loads((ROOT / "tests/fixtures/outside-20261004-parent-route-bindings.json").read_text())
PR_ROUTE_BASELINE = json.loads((ROOT / "tests/fixtures/outside-puerto-rico-prechange-routes.json").read_text())
PUERTO_RICO_REMOVALS = set(PR_ROUTE_BASELINE["removed_sources"])
PUERTO_RICO_REVIEW_SOURCES = {f"/outside/assets/owner-review/core-trips/{ref}" for ref in PR_ROUTE_BASELINE["kept_refs"]}
PUERTO_RICO_EXISTING_RECORDS = json.loads((ROOT / "tests/fixtures/outside-puerto-rico-existing-records.json").read_text())



def route_source(data, route_hash):
    match = re.fullmatch(r"#([\w-]+)(?:/([1-9]\d*))?", route_hash)
    if not match:
        return None
    route_id, ordinal = match.groups()
    studies = {item["id"]: item for item in data["studies"]}

    def first_se1(study):
        return next((image["src"] for image in study["images"] if image.get("se") == 1), None)

    def target_study_source(target, default=False):
        if not isinstance(target, dict):
            return None
        study = studies.get(target.get("studyId"))
        index = target.get("index")
        if study is None or not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(study["images"]):
            return None
        return first_se1(study) if default else study["images"][index]["src"]

    study = studies.get(route_id)
    if study is not None:
        if ordinal:
            index = min(int(ordinal) - 1, len(study["images"]) - 1)
            return study["images"][index]["src"] if study["images"] else None
        return first_se1(study)
    alias = data["aliases"].get(route_id)
    if alias is None:
        return None
    if "targets" in alias:
        if ordinal is None:
            target = alias.get("defaultTarget") if "defaultTarget" in alias else next((row for row in alias["targets"] if row is not None), None)
            return target_study_source(target, default=True)
        return target_study_source(alias["targets"][int(ordinal) - 1], default=False) if int(ordinal) <= len(alias["targets"]) else None
    study = studies.get(alias.get("studyId"))
    if ordinal is None:
        default_index = alias.get("defaultIndex", -1)
        if not study or not isinstance(default_index, int) or isinstance(default_index, bool) or not 0 <= default_index < len(study["images"]):
            return None
        return first_se1(study)
    indices = alias.get("indices", [])
    index = indices[int(ordinal) - 1] if int(ordinal) <= len(indices) else None
    return study["images"][index]["src"] if study and isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(study["images"]) else None


def default_for_source(data, source):
    if source is None:
        return None
    for study in data["studies"]:
        if any(image["src"] == source for image in study["images"]):
            return next((image["src"] for image in study["images"] if image.get("se") == 1), None)
    return None


class OutsideScoutAndRemovalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}
        cls.images = {image["src"]: image for study in cls.data["studies"] for image in study["images"]}
        # The frozen digests predate the new place/transit/display-number schema.
        # Keep the original `se` values as a separate compatibility baseline.
        legacy_data = json.loads(subprocess.check_output(
            ["git", "show", f"{LEGACY_BASELINE_REV}:src/data/outside-studies.json"],
            cwd=ROOT, text=True))
        cls.legacy_images = {image["src"]: image for study in legacy_data["studies"] for image in study["images"]}
        cls.source_display_numbers = {
            image["src"]: series["displayNumber"]
            for study in cls.data["studies"]
            for series in study["series"]
            for image in study["images"][series["start"]:series["start"] + series["count"]]
        }

    def test_final_owner_inventory_and_all_source_keyed_removals(self):
        expected = FROZEN["expected_inventory"]
        self.assertEqual((len(self.studies), len(self.images)), (expected["studies"], 413))
        baseline_sources = set(FROZEN["image_object_sha256"])
        self.assertEqual(set(self.images), (baseline_sources - REMOVED_SOURCES - NEW_REMOVALS - DUPLICATE_REMOVALS - PUERTO_RICO_REMOVALS - OWNER_EXPORT_REMOVALS) | {RESTORED_SOURCE} | PUERTO_RICO_REVIEW_SOURCES)
        self.assertEqual(len(REMOVED_SOURCES), 25)
        for source in REMOVED_SOURCES | NEW_REMOVALS | DUPLICATE_REMOVALS | PUERTO_RICO_REMOVALS | OWNER_EXPORT_REMOVALS | set(FROZEN["effective_excluded_sources"]):
            if source != RESTORED_SOURCE:
                self.assertNotIn(source, self.images, source)
        self.assertEqual(len(FROZEN["effective_excluded_sources"]), expected["effective_exclusions"])
        self.assertNotIn(RESTORED_SOURCE, FROZEN["effective_excluded_sources"])
        for source, digest in FROZEN["image_object_sha256"].items():
            if source in self.images:
                self.assertEqual(self.images[source].get("se"), self.source_display_numbers[source], source)
                if source in {f"/outside/assets/owner-review/core-trips/{ref}" for ref in ("C887", "C894")}:
                    ref = source.rsplit("/", 1)[-1]
                    actual = {key: value for key, value in self.images[source].items() if key not in {"place", "transit", "se"}}
                    expected_record = {key: value for key, value in PUERTO_RICO_EXISTING_RECORDS[ref].items() if key != "se"}
                    self.assertEqual(actual, expected_record, source)
                    continue
                # Reinsert the frozen legacy `se` only for the old-record digest:
                # current `se` is intentionally the new display number, checked above.
                actual_record = {key: value for key, value in self.images[source].items() if key not in {"place", "transit"}}
                if source in self.legacy_images:
                    actual_record["se"] = self.legacy_images[source].get("se")
                actual = hashlib.sha256(json.dumps(actual_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                self.assertEqual(actual, digest, source)
        restored = self.images[RESTORED_SOURCE]
        restored_baseline = FROZEN["authorized_restore_source"]
        self.assertEqual(self.legacy_images[RESTORED_SOURCE], restored_baseline)
        self.assertEqual({key: value for key, value in restored.items() if key not in {"place", "transit", "se"}},
                         {key: value for key, value in restored_baseline.items() if key != "se"})
        self.assertEqual(restored.get("se"), 0)
        self.assertIs(restored.get("transit"), True)
        order = [study["id"] for study in self.data["studies"]]
        self.assertEqual(order[:3], [LATEST_FLAGS["affected_studies"]["new-zealand-2026-july-photos"],
                                     LATEST_FLAGS["affected_studies"][OWNER_FLAGS["affected_studies"]["australia-2026-july-gallery"]],
                                     OWNER_FLAGS["affected_studies"]["pakistan-2026-summer-gallery"]])
        self.assertNotIn("baseball-stadium-2023-may", self.studies)

    def test_scout_series_are_zero_presentation_only_and_keep_destination_series(self):
        for spec in FROZEN["scout_contract"]:
            with self.subTest(study=spec["study_id"]):
                canonical_id = OWNER_FLAGS["affected_studies"].get(spec["canonical_id"], spec["canonical_id"])
                canonical_id = LATEST_FLAGS["affected_studies"].get(canonical_id, canonical_id)
                study = self.studies[canonical_id]
                self.assertEqual((study["date"], study["dateEnd"]), tuple(spec["study_dates"]))
                scout = study["series"][0]
                self.assertEqual(scout.get("displayNumber"), 0)
                transit_places = list(dict.fromkeys(image["place"] for image in study["images"] if image.get("transit")))
                self.assertTrue(transit_places)
                self.assertEqual(scout["title"], "SCOUT · " + ", ".join(transit_places))
                self.assertEqual((scout["date"], scout["dateEnd"]), tuple(spec["dates"]))
                retained_scout_sources = [source for source in spec["sources"] if source not in OWNER_EXPORT_REMOVALS]
                self.assertEqual((scout["start"], scout["count"], scout["key"]), (0, len(retained_scout_sources), 0))
                self.assertEqual([image["src"] for image in study["images"][:len(retained_scout_sources)]], retained_scout_sources)
                existing = study["series"][1:]
                self.assertEqual([series.get("displayNumber") for series in existing], list(range(1, len(existing) + 1)))
                self.assertTrue(all(image["transit"] for image in study["images"][:scout["count"]]))
                self.assertFalse(any(image["transit"] for image in study["images"][scout["count"]:]))
                self.assertEqual([series["start"] for series in study["series"]], sorted(series["start"] for series in study["series"]))
        pakistan = self.studies[OWNER_FLAGS["affected_studies"]["pakistan-2026-summer-gallery"]]
        australia = self.studies[LATEST_FLAGS["affected_studies"][OWNER_FLAGS["affected_studies"]["australia-2026-july-gallery"]]]
        cruise = self.studies["cruise-2024-december-gallery"]
        self.assertEqual(len(pakistan["images"]), 30)
        self.assertEqual(len(australia["images"]), 32)
        self.assertEqual(len(cruise["images"]), 8)
        self.assertEqual(pakistan["date"], "2026-06-28")
        self.assertEqual((australia["date"], australia["dateEnd"]), ("2026-07-07", "2026-07-16"))
        self.assertEqual((cruise["date"], cruise["dateEnd"]), ("2024-12-15", "2024-12-20"))
        cruise_scout = next(image for image in cruise["images"] if image["src"] == "/outside/assets/owner-review/additional-trips/A306")
        cruise_index = cruise["images"].index(cruise_scout)
        cruise_series = next(series for series in cruise["series"] if series["start"] <= cruise_index < series["start"] + series["count"])
        self.assertEqual(cruise_scout["se"], cruise_series["displayNumber"])
        self.assertTrue(cruise_scout["transit"])
        self.assertEqual(cruise_series["displayNumber"], 0)
        self.assertIn("scout", cruise_series["title"].lower())

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

    def test_all_2305_frozen_routes_keep_numbered_sources_and_se1_bare_defaults(self):
        routes = FROZEN["routes"]
        self.assertEqual(len(routes), 2305)
        self.assertEqual(len({row["hash"] for row in routes}), len(routes))
        allowed_restore = set(FROZEN["allowed_restored_routes"])
        for route in allowed_restore:
            restored_route_source = RESTORED_SOURCE if re.search(r"/[1-9]\d*$", route) else default_for_source(self.data, RESTORED_SOURCE)
            self.assertEqual(route_source(self.data, route), restored_route_source, route)
        for row in routes:
            with self.subTest(route=row["hash"]):
                expected = None if row["source"] in REMOVED_SOURCES | NEW_REMOVALS | DUPLICATE_REMOVALS | PUERTO_RICO_REMOVALS | OWNER_EXPORT_REMOVALS else row["source"]
                if row["hash"] in allowed_restore and expected is None:
                    expected = RESTORED_SOURCE if re.search(r"/[1-9]\d*$", row["hash"]) else default_for_source(self.data, RESTORED_SOURCE)
                if expected is not None and not re.search(r"/[1-9]\d*$", row["hash"]):
                    expected = default_for_source(self.data, expected)
                self.assertEqual(route_source(self.data, row["hash"]), expected, row["hash"])

    def test_parent_2540_route_bindings_preserve_numbered_sources_and_se1_bare_defaults(self):
        self.assertEqual(PARENT_ROUTES["base"], "03b49fe4bc8b340cb90c3eb1c7bdbedcbdcd5ba4")
        routes = PARENT_ROUTES["routes"]
        self.assertEqual(len(routes), 2540)
        self.assertEqual(len(set(routes)), 2540)
        self.assertEqual(NEW_REMOVALS, set(routes.values()) & NEW_REMOVALS)
        for route_hash, source in routes.items():
            with self.subTest(route=route_hash):
                expected = None if source in NEW_REMOVALS | DUPLICATE_REMOVALS | PUERTO_RICO_REMOVALS | OWNER_EXPORT_REMOVALS else source
                if expected is not None and not re.search(r"/[1-9]\d*$", route_hash):
                    expected = default_for_source(self.data, expected)
                self.assertEqual(route_source(self.data, route_hash), expected, route_hash)


if __name__ == "__main__":
    unittest.main()
