import copy
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
BASELINE = json.loads((ROOT / "tests/fixtures/outside-place-baseline.json").read_text())
FOCUS_IDS = {
    "new-zealand-2026-july-photos-161007",
    "australia-2026-july-gallery-20261005-quokka",
    "pakistan-2026-summer-gallery-20261005",
    "galapagos-2026-january-photos-20261004-20261005-161007",
    "montreal-november-2025-photos-20261005",
    "american-southwest-2025-october-gallery-20261004-2-20261005",
}
ROTTNEST_QUOKKA_SOURCE = "/outside/assets/owner-review/summer-2026/S0659"
OLD_AUSTRALIA_ID = "australia-2026-july-gallery-20261005-161007"
AUSTRALIA_ID = "australia-2026-july-gallery-20261005-quokka"


class OutsidePlaceDataTests(unittest.TestCase):
    def test_every_record_has_explicit_place_transit_and_display_number_without_public_gps(self):
        for study in DATA["studies"]:
            for image in study["images"]:
                self.assertIsInstance(image.get("place"), str, (study["id"], image["src"]))
                self.assertTrue(image["place"].strip(), (study["id"], image["src"]))
                self.assertIs(type(image.get("transit")), bool, (study["id"], image["src"]))
                self.assertIs(type(image.get("se")), int, (study["id"], image["src"]))
                self.assertEqual(image["se"] == 0, image["transit"], (study["id"], image["src"]))
                self.assertFalse({"gps", "lat", "latitude", "lon", "lng", "longitude"} & image.keys())

    def test_series_partition_images_and_agree_with_image_display_numbers(self):
        for study in DATA["studies"]:
            ordered = sorted(study["series"], key=lambda series: series["start"])
            next_image = 0
            display_numbers = []
            for series in ordered:
                self.assertIs(type(series.get("displayNumber")), int, (study["id"], series))
                display_numbers.append(series["displayNumber"])
                self.assertEqual(series["start"], next_image, (study["id"], series))
                self.assertGreater(series["count"], 0, (study["id"], series))
                images = study["images"][series["start"]:series["start"] + series["count"]]
                self.assertEqual(len(images), series["count"], (study["id"], series))
                self.assertTrue(all(image["se"] == series["displayNumber"] for image in images), (study["id"], series))
                self.assertEqual(series["displayNumber"] == 0, all(image["transit"] for image in images))
                next_image += series["count"]
            self.assertEqual(next_image, len(study["images"]), study["id"])
            self.assertEqual(len(display_numbers), len(set(display_numbers)), study["id"])
            self.assertEqual(display_numbers.count(0), 1 if any(image["transit"] for image in study["images"]) else 0, study["id"])
            self.assertEqual(display_numbers[0] == 0, any(image["transit"] for image in study["images"]), study["id"])
            transit_study = any(image["transit"] for image in study["images"])
            expected_numbers = ([0] + list(range(1, len(display_numbers))) if transit_study else list(range(1, len(display_numbers) + 1)))
            self.assertEqual(display_numbers, expected_numbers, study["id"])
            self.assertFalse(study["images"][study["key"]]["transit"], study["id"])

    def test_date_area_groups_are_chronological_and_consecutive_in_focus_studies(self):
        for study in DATA["studies"]:
            if study["id"] not in FOCUS_IDS:
                continue
            transit = [image for image in study["images"] if image["transit"]]
            ordinary = [image for image in study["images"] if not image["transit"]]
            self.assertEqual(transit, study["images"][:len(transit)], study["id"])
            self.assertEqual(
                [(image.get("d", ""), image.get("t", "")) for image in transit],
                sorted((image.get("d", ""), image.get("t", "")) for image in transit),
                study["id"],
            )
            self.assertEqual(
                [(image.get("d", ""), image.get("t", "")) for image in ordinary],
                sorted((image.get("d", ""), image.get("t", "")) for image in ordinary),
                study["id"],
            )
            if transit:
                self.assertEqual(study["date"], min(image["d"] for image in ordinary), study["id"])
                self.assertEqual(study["dateEnd"], max(image["d"] for image in ordinary), study["id"])
            expected = []
            for image in ordinary:
                pair = (image.get("d", ""), image["area"])
                if not expected or expected[-1][0] != pair:
                    expected.append([pair, 0])
                expected[-1][1] += 1
            actual = []
            for series in sorted(study["series"], key=lambda item: item["start"]):
                if series["displayNumber"] == 0:
                    self.assertTrue(transit, study["id"])
                    self.assertEqual(series["start"], 0, study["id"])
                    continue
                images = study["images"][series["start"]:series["start"] + series["count"]]
                self.assertEqual(len({image.get("d", "") for image in images}), 1, (study["id"], series))
                self.assertEqual(len({image["area"] for image in images}), 1, (study["id"], series))
                actual.append([(images[0].get("d", ""), images[0]["area"]), len(images)])
            self.assertEqual(actual, expected, study["id"])

    def test_transit_places_and_se0_are_limited_to_authorized_itineraries(self):
        transit = {
            study["id"]: [image for image in study["images"] if image["transit"]]
            for study in DATA["studies"]
            if any(image.get("transit") for image in study["images"])
        }
        self.assertEqual(set(transit), {
            AUSTRALIA_ID,
            "pakistan-2026-summer-gallery-20261005",
            "cruise-2024-december-gallery",
        })
        australia = transit[AUSTRALIA_ID]
        self.assertEqual([(image["place"], image["se"]) for image in australia], [("Bangkok", 0)])
        pakistan = transit["pakistan-2026-summer-gallery-20261005"]
        self.assertEqual(len(pakistan), 11)
        self.assertEqual(set(image["place"] for image in pakistan), {"Rome", "Tirana"})
        self.assertTrue(all(image["se"] == 0 for image in pakistan))
        self.assertEqual(australia[0]["src"], "/outside/assets/owner-review/additional-trips/A278")
        self.assertEqual(pakistan, next(study for study in DATA["studies"] if study["id"] == "pakistan-2026-summer-gallery-20261005")["images"][:11])

    def test_focus_place_names_are_supported_and_no_southwest_las_vegas_is_invented(self):
        studies = {study["id"]: study for study in DATA["studies"]}
        self.assertEqual(
            {image["place"] for image in studies["new-zealand-2026-july-photos-161007"]["images"]},
            {"Auckland", "Rotorua", "Waiotapu"},
        )
        self.assertEqual(
            {image["place"] for image in studies[AUSTRALIA_ID]["images"]},
            {"Bangkok", "Busselton", "Dunsborough", "Yallingup", "Rottnest Island", "Margaret River", "Augusta", "Hamelin Bay", "Perth"},
        )
        self.assertEqual(
            {image["place"] for image in studies["pakistan-2026-summer-gallery-20261005"]["images"]},
            {"Rome", "Tirana", "Karachi", "Murree", "Nathia Gali", "Islamabad", "Lahore"},
        )
        self.assertEqual(
            {image["place"] for image in studies["galapagos-2026-january-photos-20261004-20261005-161007"]["images"]},
            {"Santa Cruz", "Isabela", "San Cristóbal"},
        )
        self.assertEqual(
            {image["place"] for image in studies["american-southwest-2025-october-gallery-20261004-2-20261005"]["images"]},
            {"Joshua Tree", "Grand Canyon", "Zion", "Hoover Dam"},
        )
        self.assertNotIn("Las Vegas", {image["place"] for image in studies["american-southwest-2025-october-gallery-20261004-2-20261005"]["images"]})

    def test_gps_interpretation_corrects_reporoa_and_maps_supported_regions(self):
        studies = {study["id"]: study for study in DATA["studies"]}
        nz = {image["src"]: image for image in studies["new-zealand-2026-july-photos-161007"]["images"]}
        self.assertEqual(nz["/outside/assets/owner-review/summer-2026/S1059"]["place"], "Waiotapu")
        self.assertEqual(nz["/outside/assets/owner-review/summer-2026/S1108"]["place"], "Waiotapu")
        galapagos = studies["galapagos-2026-january-photos-20261004-20261005-161007"]
        self.assertEqual(galapagos["images"][0]["place"], "Santa Cruz")
        southwest = studies["american-southwest-2025-october-gallery-20261004-2-20261005"]
        self.assertEqual(southwest["images"][-1]["place"], "Hoover Dam")
        self.assertEqual(southwest["images"][-1]["transit"], False)

    def test_hidden_studies_use_the_same_maximal_date_area_runs(self):
        for study in DATA["studies"]:
            previous = None
            for series in study["series"]:
                if series["displayNumber"] == 0:
                    continue
                segment = study["images"][series["start"]:series["start"] + series["count"]]
                pairs = {(im.get("d", ""), im["area"]) for im in segment}
                self.assertEqual(len(pairs), 1, study["id"])
                pair = next(iter(pairs))
                self.assertNotEqual(previous, pair, study["id"])
                previous = pair

    def test_existing_hidden_cruise_scout_remains_transit_without_reordering_routes(self):
        cruise = next(s for s in DATA["studies"] if s["id"] == "cruise-2024-december-gallery")
        self.assertEqual(cruise["images"][0]["src"], "/outside/assets/owner-review/additional-trips/A306")
        self.assertTrue(cruise["images"][0]["transit"])
        self.assertEqual(cruise["images"][0]["se"], 0)
        self.assertFalse(cruise["images"][cruise["key"]]["transit"])

    def test_unknown_europe_city_is_explicit_not_inherited_study_location(self):
        europe = next(s for s in DATA["studies"] if s["id"] == "europe-shared-album")
        self.assertEqual({im["place"] for im in europe["images"]}, {"Location unconfirmed"})
        self.assertEqual((europe["date"], europe["dateEnd"]), ("", ""))

    def test_study_image_identities_dates_and_alias_targets_match_frozen_baseline(self):
        expected_studies = BASELINE["studies"]
        actual_studies = DATA["studies"]
        self.assertEqual(len(actual_studies), 21)
        self.assertEqual(sum(len(study["images"]) for study in actual_studies), 414)
        self.assertEqual([study["id"] for study in actual_studies],
                         [AUSTRALIA_ID if row["id"] == OLD_AUSTRALIA_ID else row["id"] for row in expected_studies])
        for study, expected in zip(actual_studies, expected_studies):
            expected_sources = list(expected["srcs"])
            expected_date_times = list(expected["date_time_tz"])
            if study["id"] == AUSTRALIA_ID:
                expected_sources.insert(14, ROTTNEST_QUOKKA_SOURCE)
                expected_date_times.insert(14, ["2026-07-11", "11:30:03", "UTC+08:00"])
            self.assertEqual([image["src"] for image in study["images"]], expected_sources, study["id"])
            self.assertEqual(
                [[image.get("d"), image.get("t"), image.get("tz")] for image in study["images"]],
                expected_date_times,
                study["id"],
            )
        rebased_aliases = copy.deepcopy(DATA["aliases"])
        rebased_aliases.pop(OLD_AUSTRALIA_ID)
        for alias in rebased_aliases.values():
            if isinstance(alias.get("targets"), list):
                for target in alias["targets"]:
                    if isinstance(target, dict) and target.get("studyId") == AUSTRALIA_ID:
                        target["studyId"] = OLD_AUSTRALIA_ID
                        if target.get("index", -1) >= 15:
                            target["index"] -= 1
                default = alias.get("defaultTarget")
                if isinstance(default, dict) and default.get("studyId") == AUSTRALIA_ID:
                    default["studyId"] = OLD_AUSTRALIA_ID
                    if default.get("index", -1) >= 15:
                        default["index"] -= 1
            elif alias.get("studyId") == AUSTRALIA_ID:
                alias["studyId"] = OLD_AUSTRALIA_ID
                alias["indices"] = [index - 1 if isinstance(index, int) and not isinstance(index, bool) and index >= 15 else index
                                    for index in alias.get("indices", [])]
                if isinstance(alias.get("defaultIndex"), int) and alias["defaultIndex"] >= 15:
                    alias["defaultIndex"] -= 1
        alias_payload = json.dumps(rebased_aliases, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(alias_payload).hexdigest(), BASELINE["aliases_sha256"])


if __name__ == "__main__":
    unittest.main()
