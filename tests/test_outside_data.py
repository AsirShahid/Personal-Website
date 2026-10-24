"""Outside Studies data checks that stay valid when photos are added or removed.

Run with `python -m pytest tests/test_outside_data.py -q` (about a second). Nothing here pins photo
counts, positions or study lists, so ordinary content edits need no test changes.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from collections import defaultdict
from pathlib import Path

from outside_links import LEGACY, RENAMED, first_se1_index, photo_id, resolve, study_ids

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
REMOVED = set(json.loads((ROOT / "src/data/outside-removed-sources.json").read_text()))
IDS_AT_FREEZE = json.loads((ROOT / "tests/fixtures/outside-photo-ids-at-freeze.json").read_text())
LINKS_AT_FREEZE = json.loads((ROOT / "tests/fixtures/outside-links-at-freeze.json").read_text())
PUBLIC = ROOT / "public"
PRIVATE_KEYS = {"gps", "lat", "latitude", "lon", "lng", "longitude", "archive_id", "asset_id", "drive_id", "filename"}
# C917 shows a receipt; its public copies carry a privacy mask. If the photo is kept, those exact bytes must stay.
MASKED = {"/outside/assets/owner-review/core-trips/C917": {
    "s": "b7260afdde2ccdffbcf29fa3ddf0afc41ea18f2819d2ce74a409beffd8aaca2e",
    "m": "f5220748f2cc67d97790b213e62f2b8bbedebbf00b462f92ae3522c819dce028",
    "l": "5102a09cb9ced8608caa7518f763a4024f109381d363ce999049570a646ed525"}}

STUDIES = {study["id"]: study for study in DATA["studies"]}
IMAGES = [(study, k, image) for study in DATA["studies"] for k, image in enumerate(study["images"])]


class OutsideDataTests(unittest.TestCase):
    def test_every_photo_has_a_unique_stable_id_and_source(self):
        ids = [image["id"] for _, _, image in IMAGES]
        srcs = [image["src"] for _, _, image in IMAGES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(srcs), len(set(srcs)))
        for _, _, image in IMAGES:
            self.assertRegex(image["id"], r"^p[0-9a-f]{8}$")
            self.assertEqual(image["id"], photo_id(image["src"]), image["src"])

    def test_ids_already_in_links_never_change(self):
        for _, _, image in IMAGES:
            if image["id"] in IDS_AT_FREEZE:
                self.assertEqual(IDS_AT_FREEZE[image["id"]], image["src"], image["id"])

    def test_every_photo_has_its_three_web_sizes(self):
        for _, _, image in IMAGES:
            for size in "sml":
                self.assertTrue((PUBLIC / f"{image['src'].lstrip('/')}-{size}.webp").is_file(), f"{image['src']}-{size}.webp")

    def test_no_duplicate_photos(self):
        owners = defaultdict(list)
        for _, _, image in IMAGES:
            owners[hashlib.sha256((PUBLIC / f"{image['src'].lstrip('/')}-m.webp").read_bytes()).hexdigest()].append(image["src"])
        self.assertEqual({k: v for k, v in owners.items() if len(v) > 1}, {})

    def test_masked_receipt_photo_keeps_its_privacy_mask(self):
        present = {image["src"] for _, _, image in IMAGES}
        for src, hashes in MASKED.items():
            if src in present:
                for size, digest in hashes.items():
                    self.assertEqual(hashlib.sha256((PUBLIC / f"{src.lstrip('/')}-{size}.webp").read_bytes()).hexdigest(), digest, size)

    def test_removed_photos_stay_removed(self):
        present = {image["src"] for _, _, image in IMAGES}
        self.assertEqual(present & REMOVED, set())

    def test_only_hashed_build_output_is_cached_forever(self):
        # A replaced photo keeps its URL, so photos must revalidate; only content-hashed /_astro/ files may be immutable.
        rules, current = {}, None
        for line in (PUBLIC / "_headers").read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if not line[0].isspace():
                current = line.strip()
                rules[current] = []
            elif current:
                rules[current].append(line.strip().lower())
        immutable = sorted(path for path, headers in rules.items() if any(h.startswith("cache-control:") and "immutable" in h for h in headers))
        self.assertEqual(immutable, ["/_astro/*"])

    def test_every_place_has_an_area(self):
        for study in DATA["studies"]:
            area_map = study.get("areaMap", {})
            for image in study["images"]:
                self.assertIn(image["place"], area_map, (study["id"], image["src"]))
                self.assertEqual(image.get("area"), area_map[image["place"]], (study["id"], image["src"]))

    def test_public_records_carry_no_location_coordinates_or_archive_ids(self):
        for _, _, image in IMAGES:
            self.assertFalse(PRIVATE_KEYS & image.keys(), image["src"])
            self.assertIs(type(image.get("transit")), bool, image["src"])
            self.assertTrue(str(image.get("place", "")).strip(), image["src"])

    def test_series_partition_each_study_into_date_and_area_runs(self):
        for study in DATA["studies"]:
            with self.subTest(study=study["id"]):
                images = study["images"]
                self.assertTrue(images)
                self.assertTrue(0 <= study["key"] < len(images))
                self.assertFalse(images[study["key"]]["transit"])
                transit = sum(image["transit"] for image in images)
                self.assertFalse(any(image["transit"] for image in images[transit:]), "transit photos lead the study")
                cursor, previous = 0, None
                for number, series in enumerate(study["series"], 0 if transit else 1):
                    self.assertEqual((series["start"], series["displayNumber"]), (cursor, number))
                    run = images[cursor:cursor + series["count"]]
                    self.assertTrue(run)
                    self.assertTrue(series["start"] <= series["key"] < series["start"] + series["count"])
                    self.assertTrue(all(image["se"] == number for image in run))
                    if number:
                        groups = {(image.get("d", ""), image.get("area")) for image in run}
                        self.assertEqual(len(groups), 1)
                        self.assertNotEqual(groups, {previous})
                        previous = next(iter(groups))
                    cursor += series["count"]
                self.assertEqual(cursor, len(images))

    def test_studies_are_newest_first(self):
        order = [study["id"] for study in DATA["studies"]]
        newest = sorted(DATA["studies"], key=lambda s: (s.get("dateEnd") or s.get("date") or "", s.get("date") or ""), reverse=True)
        self.assertEqual(order, [study["id"] for study in newest])

    def test_old_links_open_the_same_photo_or_say_unavailable(self):
        """Every link that existed when ids were introduced keeps its photo, or is unavailable if that photo was removed."""
        present = {image["src"] for _, _, image in IMAGES}
        for link, (kind, value) in LINKS_AT_FREEZE.items():
            actual = resolve(link)
            if kind == "photo":
                expected = value if value in present else None
            elif kind == "study":
                study = STUDIES.get(RENAMED.get(value, value))
                expected = study["images"][first_se1_index(study)]["src"] if study else None
            else:
                expected = None
            self.assertEqual(actual, expected, link)

    def test_legacy_links_only_point_at_known_ids(self):
        known = set(IDS_AT_FREEZE)
        for route_id, old in LEGACY.items():
            self.assertNotIn(route_id, {"", "p"}, route_id)
            self.assertTrue(set(filter(None, old["photos"])) <= known, route_id)

    def test_study_ids_follow_the_naming_rule(self):
        """<place>-<year>-<month> from the shown name and first day; see scripts/outside.py. Fix with rename-studies."""
        self.assertEqual({old: new for old, new in study_ids(DATA).items() if old != new}, {})
        for study in DATA["studies"]:
            self.assertRegex(study["id"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertNotRegex(study["id"], r"20\d{6}|gallery|photos|album", "ids never carry batch names or import dates")

    def test_renamed_study_ids_still_open_their_study(self):
        for old, new in RENAMED.items():
            self.assertIn(new, STUDIES, f"{old} redirects to a study that no longer exists")
            self.assertNotIn(old, STUDIES, f"{old} is a current id again; drop it from outside-study-renames.json")
            study = STUDIES[new]
            self.assertEqual(resolve(f"#{old}"), study["images"][first_se1_index(study)]["src"], old)
            self.assertEqual(resolve(f"#{old}/{study['images'][-1]['id']}"), study["images"][-1]["src"], old)

    def test_a_current_id_that_is_also_an_old_link_opens_the_same_study(self):
        # Old link ids win over current ids when the page resolves a link, so they must agree.
        for study_id in STUDIES:
            old = LEGACY.get(study_id)
            if old is not None:
                self.assertEqual(RENAMED.get(old["study"], old["study"]), study_id, study_id)

    def test_content_script_rebuild_matches_stored_series_and_covers(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/outside.py"), "check"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
