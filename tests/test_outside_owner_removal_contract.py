import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
OWNER_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005.json").read_text())
LATEST_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005-161007.json").read_text())


def target_source(data, target):
    if not isinstance(target, dict):
        return None
    study = next((row for row in data["studies"] if row["id"] == target.get("studyId")), None)
    index = target.get("index")
    if study is None or not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(study["images"]):
        return None
    return study["images"][index]["src"]


def route_bindings(data, route_id):
    studies = {row["id"]: row for row in data["studies"]}

    def first_se1(study):
        return next((image["src"] for image in study["images"] if image.get("se") == 1), None) if study else None

    study = studies.get(route_id)
    if study is not None:
        targets = [image["src"] for image in study["images"]]
        return {"default": first_se1(study), "targets": targets}
    alias = data["aliases"].get(route_id)
    if alias is None:
        return None
    if isinstance(alias.get("targets"), list):
        targets = [target_source(data, target) for target in alias["targets"]]
        default_target = alias.get("defaultTarget") if "defaultTarget" in alias else next((target for target in alias["targets"] if target is not None), None)
        valid_default = target_source(data, default_target) is not None
        target_study = studies.get(default_target.get("studyId")) if isinstance(default_target, dict) else None
        return {"default": first_se1(target_study) if valid_default else None, "targets": targets}
    study = studies.get(alias.get("studyId"))
    indices = alias.get("indices", [])
    targets = [study["images"][index]["src"] if study and isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(study["images"]) else None for index in indices]
    default_index = alias.get("defaultIndex")
    if default_index is None:
        default_index = next((index for index in indices if isinstance(index, int) and not isinstance(index, bool) and index >= 0), None)
    valid_default = study and isinstance(default_index, int) and not isinstance(default_index, bool) and 0 <= default_index < len(study["images"])
    return {"default": first_se1(study) if valid_default else None, "targets": targets}


def first_se1_for_source(data, source):
    if source is None:
        return None
    for study in data["studies"]:
        if any(image["src"] == source for image in study["images"]):
            return next((image["src"] for image in study["images"] if image.get("se") == 1), None)
    return None


class OwnerPhotoRemovalContractTests(unittest.TestCase):
    def test_exact_owner_flag_sources_are_removed_without_changing_study_count(self):
        self.assertEqual(OWNER_FLAGS["export_sha256"], "767d747d52f02a44eb4132cb143f2e75bf5a7a0b1f4b7a9eb3088d6fa0023c53")
        flagged = OWNER_FLAGS["flagged_sources"]
        self.assertEqual((OWNER_FLAGS["flagged_count"], len(flagged), len(set(flagged))), (45, 45, 45))
        photos = {image["src"] for study in DATA["studies"] for image in study["images"]}
        self.assertEqual(set(flagged) & photos, set(), "every source in the frozen owner export must be unavailable")
        self.assertEqual((len(DATA["studies"]), len(photos)), (21, 413))

    def test_latest_six_owner_flags_are_removed_without_other_photo_cuts(self):
        newly_flagged = set(LATEST_FLAGS["newly_flagged_sources"])
        self.assertEqual((LATEST_FLAGS["export_sha256"], LATEST_FLAGS["flagged_count"], len(LATEST_FLAGS["flagged_sources"])),
                         ("948f2a9f4522807b4cefffdabe6b84da33d8cffd61e99c2783d7b642988acff4", 65, 65))
        photos = {image["src"] for study in DATA["studies"] for image in study["images"]}
        self.assertEqual(photos & newly_flagged, set(), "the six newly flagged sources must be unavailable")
        self.assertEqual(photos & set(LATEST_FLAGS["historically_absent_sources"]), set(), "previously removed sources must remain unavailable")
        self.assertEqual(set(LATEST_FLAGS["flagged_sources"]), newly_flagged | set(LATEST_FLAGS["historically_absent_sources"]))
        self.assertEqual((len(DATA["studies"]), len(photos)), (21, 413))

    def test_every_affected_canonical_and_alias_route_keeps_its_source_or_is_unavailable(self):
        flagged = set(OWNER_FLAGS["flagged_sources"]) | set(LATEST_FLAGS["newly_flagged_sources"])
        studies = {study["id"]: study for study in DATA["studies"]}
        for old_id, new_id in OWNER_FLAGS["affected_studies"].items():
            with self.subTest(canonical=old_id):
                before = OWNER_FLAGS["before_canonical_bindings"][old_id]
                retained = [source for source in before["targets"] if source not in flagged]
                new_id = LATEST_FLAGS["affected_studies"].get(new_id, new_id)
                self.assertIn(new_id, studies)
                self.assertEqual([image["src"] for image in studies[new_id]["images"]], retained)
                self.assertIn(old_id, DATA["aliases"])
                expected = {"default": first_se1_for_source(DATA, before["default"]) if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, old_id), expected)
        for alias_id, before in OWNER_FLAGS["before_alias_bindings"].items():
            with self.subTest(alias=alias_id):
                expected = {"default": first_se1_for_source(DATA, before["default"]) if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, alias_id), expected)

    def test_latest_canonical_and_alias_ordinals_follow_source_identity(self):
        flagged = set(LATEST_FLAGS["newly_flagged_sources"])
        studies = {study["id"]: study for study in DATA["studies"]}
        for old_id, new_id in LATEST_FLAGS["affected_studies"].items():
            with self.subTest(canonical=old_id):
                before = LATEST_FLAGS["before_canonical_bindings"][old_id]
                self.assertEqual([image["src"] for image in studies[new_id]["images"]],
                                 [source for source in before["targets"] if source not in flagged])
                expected = {"default": first_se1_for_source(DATA, before["default"]) if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, old_id), expected)
        for alias_id, before in LATEST_FLAGS["before_alias_bindings"].items():
            with self.subTest(alias=alias_id):
                expected = {"default": first_se1_for_source(DATA, before["default"]) if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, alias_id), expected)


if __name__ == "__main__":
    unittest.main()
