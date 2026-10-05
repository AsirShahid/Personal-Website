import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
OWNER_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005.json").read_text())


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
    study = studies.get(route_id)
    if study is not None:
        targets = [image["src"] for image in study["images"]]
        return {"default": targets[0] if targets else None, "targets": targets}
    alias = data["aliases"].get(route_id)
    if alias is None:
        return None
    if isinstance(alias.get("targets"), list):
        targets = [target_source(data, target) for target in alias["targets"]]
        default = alias.get("defaultTarget") if "defaultTarget" in alias else next((target for target in alias["targets"] if target is not None), None)
        return {"default": target_source(data, default), "targets": targets}
    study = studies.get(alias.get("studyId"))
    indices = alias.get("indices", [])
    targets = [study["images"][index]["src"] if study and isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(study["images"]) else None for index in indices]
    default_index = alias.get("defaultIndex")
    if default_index is None:
        default_index = next((index for index in indices if isinstance(index, int) and not isinstance(index, bool) and index >= 0), None)
    default = study["images"][default_index]["src"] if study and isinstance(default_index, int) and not isinstance(default_index, bool) and 0 <= default_index < len(study["images"]) else None
    return {"default": default, "targets": targets}


class OwnerPhotoRemovalContractTests(unittest.TestCase):
    def test_exact_owner_flag_sources_are_removed_without_changing_study_count(self):
        self.assertEqual(OWNER_FLAGS["export_sha256"], "767d747d52f02a44eb4132cb143f2e75bf5a7a0b1f4b7a9eb3088d6fa0023c53")
        flagged = OWNER_FLAGS["flagged_sources"]
        self.assertEqual((OWNER_FLAGS["flagged_count"], len(flagged), len(set(flagged))), (45, 45, 45))
        photos = {image["src"] for study in DATA["studies"] for image in study["images"]}
        self.assertEqual(set(flagged) & photos, set(), "every source in the frozen owner export must be unavailable")
        self.assertEqual((len(DATA["studies"]), len(photos)), (21, 419))

    def test_every_affected_canonical_and_alias_route_keeps_its_source_or_is_unavailable(self):
        flagged = set(OWNER_FLAGS["flagged_sources"])
        studies = {study["id"]: study for study in DATA["studies"]}
        for old_id, new_id in OWNER_FLAGS["affected_studies"].items():
            with self.subTest(canonical=old_id):
                before = OWNER_FLAGS["before_canonical_bindings"][old_id]
                retained = [source for source in before["targets"] if source not in flagged]
                self.assertIn(new_id, studies)
                self.assertEqual([image["src"] for image in studies[new_id]["images"]], retained)
                self.assertIn(old_id, DATA["aliases"])
                expected = {"default": before["default"] if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, old_id), expected)
        for alias_id, before in OWNER_FLAGS["before_alias_bindings"].items():
            with self.subTest(alias=alias_id):
                expected = {"default": before["default"] if before["default"] not in flagged else None,
                            "targets": [source if source not in flagged else None for source in before["targets"]]}
                self.assertEqual(route_bindings(DATA, alias_id), expected)


if __name__ == "__main__":
    unittest.main()
