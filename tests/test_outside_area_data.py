import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
AREA_FIXTURE = json.loads((ROOT / "tests/fixtures/outside-area-map-baseline.json").read_text())
BASELINE_COVERS = json.loads((ROOT / "tests/fixtures/outside-area-cover-baseline.json").read_text())
PLACE_BASELINE = json.loads((ROOT / "tests/fixtures/outside-area-source-baseline.json").read_text())


class OutsideAreaDataTests(unittest.TestCase):
    def test_every_study_has_its_explicit_area_map_and_requested_order(self):
        studies = {study["id"]: study for study in DATA["studies"]}
        self.assertEqual(set(studies), set(AREA_FIXTURE))
        self.assertEqual(len(DATA["studies"]), 21)
        self.assertEqual(sum(len(study["images"]) for study in DATA["studies"]), 414)
        for study_id, expected in AREA_FIXTURE.items():
            study = studies[study_id]
            with self.subTest(study=study_id):
                self.assertEqual(study.get("areaMap"), expected["areaMap"])
                self.assertEqual(study.get("areaOrder"), expected["areaOrder"])
                self.assertTrue({image["place"] for image in study["images"]} <= set(study["areaMap"]))
                self.assertEqual(len(study["areaOrder"]), len(set(study["areaOrder"])))
                for image in study["images"]:
                    self.assertEqual(image.get("area"), study["areaMap"][image["place"]], image["src"])
                    self.assertFalse({"gps", "lat", "latitude", "lon", "lng", "longitude"} & image.keys())
        self.assertEqual(set(BASELINE_COVERS), set(studies))
        for study_id, cover in BASELINE_COVERS.items():
            study = studies[study_id]
            self.assertEqual(study["key"], cover["key"], study_id)
            self.assertEqual(study["images"][study["key"]]["src"], cover["src"], study_id)

    def test_series_are_maximal_consecutive_date_area_runs_with_one_transit_series(self):
        for study in DATA["studies"]:
            ordered = sorted(study["series"], key=lambda row: row["start"])
            self.assertEqual(ordered[0]["start"], 0, study["id"])
            cursor = 0
            ordinary_runs = []
            previous = None
            transit_rows = []
            for series in ordered:
                images = study["images"][series["start"]:series["start"] + series["count"]]
                self.assertEqual(series["start"], cursor, study["id"])
                self.assertEqual(len(images), series["count"], study["id"])
                self.assertGreater(series["count"], 0, study["id"])
                original = next(s for s in PLACE_BASELINE["studies"] if s["id"] == study["id"])
                keys = [row["key"] for row in original["series"]
                        if series["start"] <= row["key"] < series["start"] + series["count"]]
                self.assertEqual(series["key"], keys[0] if keys else series["start"])
                self.assertTrue(all(image["se"] == series["displayNumber"] for image in images), study["id"])
                cursor += series["count"]
                if series["displayNumber"] == 0:
                    transit_rows.append(series)
                    self.assertEqual(series["start"], 0, study["id"])
                    self.assertTrue(all(image["transit"] for image in images), study["id"])
                    self.assertEqual(series["title"], "SCOUT · " + ", ".join(dict.fromkeys(image["place"] for image in images)))
                    continue
                self.assertTrue(all(not image["transit"] for image in images), study["id"])
                group = {(image.get("d", ""), image["area"]) for image in images}
                self.assertEqual(len(group), 1, (study["id"], series))
                pair = next(iter(group))
                self.assertNotEqual(previous, pair, (study["id"], "adjacent equal date/area runs were not merged"))
                previous = pair
                self.assertEqual(series.get("date", ""), images[0].get("d", ""), study["id"])
                self.assertEqual(series.get("dateEnd", ""), images[-1].get("d", ""), study["id"])
                ordinary_runs.append((pair, len(images)))
            self.assertEqual(cursor, len(study["images"]), study["id"])
            self.assertEqual(len(transit_rows), int(any(image["transit"] for image in study["images"])), study["id"])
            ordinary = [image for image in study["images"] if not image["transit"]]
            expected_runs = []
            for image in ordinary:
                pair = (image.get("d", ""), image["area"])
                if not expected_runs or expected_runs[-1][0] != pair:
                    expected_runs.append([pair, 0])
                expected_runs[-1][1] += 1
            self.assertEqual(ordinary_runs, [tuple(row) for row in expected_runs], study["id"])

    def test_area_migration_preserves_source_date_time_zone_and_alias_identity(self):
        baseline = {row["id"]: row for row in PLACE_BASELINE["studies"]}
        for study in DATA["studies"]:
            before = baseline[study["id"]]
            with self.subTest(study=study["id"]):
                self.assertEqual([image["src"] for image in study["images"]], before["srcs"])
                immutable = [{k: v for k, v in image.items() if k not in ("area", "se")}
                             for image in study["images"]]
                digest = hashlib.sha256(json.dumps(immutable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                self.assertEqual(digest, before["immutable_images_sha256"])
                self.assertEqual(study["images"][study["key"]]["src"], before["cover_src"])
                self.assertEqual(next(i["src"] for i in study["images"] if i["se"] == 1), before["first_se1_src"])
                self.assertEqual([[image.get("d"), image.get("t"), image.get("tz")] for image in study["images"]], before["date_time_tz"])
        aliases = json.dumps(DATA["aliases"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(aliases).hexdigest(), PLACE_BASELINE["aliases_sha256"])

    def test_australia_july_thirteenth_small_places_coalesce_into_south_west(self):
        australia = next(study for study in DATA["studies"] if study["id"] == "australia-2026-july-gallery-20261005-quokka")
        july_13 = [image for image in australia["images"] if image.get("d") == "2026-07-13"]
        self.assertGreater(len({image["place"] for image in july_13}), 1)
        self.assertEqual({image["area"] for image in july_13}, {"South West"})
        first_index = australia["images"].index(july_13[0])
        series = next(row for row in australia["series"]
                      if row["start"] <= first_index < row["start"] + row["count"])
        self.assertEqual(series["count"], len(july_13))
        self.assertEqual(series["date"], "2026-07-13")

    def test_albania_transit_uses_tirana_as_place_and_area(self):
        pakistan = next(study for study in DATA["studies"] if study["id"] == "pakistan-2026-summer-gallery-20261005")
        albania = [image for image in pakistan["images"] if image["transit"] and image["place"] == "Tirana"]
        self.assertTrue(albania)
        self.assertTrue(all(image["area"] == "Tirana" for image in albania))
        self.assertFalse(any(image["place"] == "Albania" for image in pakistan["images"]))

    def test_migration_check_is_idempotent_and_reports_data_drift_without_rewriting(self):
        script = ROOT / "scripts/migrate_outside_area_series.py"
        check = subprocess.run([sys.executable, str(script), "--check"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        payload = json.loads((ROOT / "src/data/outside-studies.json").read_text())
        payload["studies"][0]["images"][0]["area"] = "Deliberate drift"
        with tempfile.TemporaryDirectory() as directory:
            drifted = Path(directory) / "outside-studies.json"
            drifted.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            check = subprocess.run([sys.executable, str(script), "--check", "--data", str(drifted)],
                                   cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(check.returncode, 1)
            self.assertIn("drift detected", check.stderr)
            self.assertEqual(json.loads(drifted.read_text())["studies"][0]["images"][0]["area"], "Deliberate drift")


if __name__ == "__main__":
    unittest.main()
