import hashlib
import json
import re
import unittest
from pathlib import Path

DATA = Path(__file__).parents[1] / "src/data/outside-studies.json"
HISTORICAL_ROUTES = Path(__file__).parent / "fixtures/outside-historical-route-contract.json"
OWNER_REMOVALS = {
    "/outside/assets/owner-review/core-trips/C538",
    "/outside/assets/owner-review/core-trips/C542",
    "/outside/assets/owner-review/core-trips/C941",
    "/outside/hoover-dam/005",
    "/outside/study-0726/006",
    "/outside/assets/montreal-august-2023/ma23-529f8c72a5bc4f7c3233",
    "/outside/assets/montreal-august-2023/ma23-77102b8052d5329f34fe",
    "/outside/assets/montreal-august-2023/ma23-adfdada258f2899fa661",
    "/outside/assets/montreal-august-2023/ma23-cecf837cb46c302e41d9",
    "/outside/assets/montreal-august-2023/ma23-d3097e97c5181359d2bb",
    "/outside/assets/montreal-august-2023/ma23-dd73c12b9fbfd26ca850",
    "/outside/assets/montreal-august-2023/ma23-f8b5712820c2df7c08c6",
}


class OutsideContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.studies = {study["id"]: study for study in cls.data["studies"]}
        cls.sources = {image["src"] for study in cls.data["studies"] for image in study["images"]}

    def test_final_inventory_and_readable_non_reused_canonical_ids(self):
        ids = set(self.studies)
        self.assertEqual((len(ids), sum(len(s["images"]) for s in self.studies.values())), (25, 473))
        for study_id in ids:
            self.assertRegex(study_id, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertFalse(re.search(r"projection|metadata|retained|expanded|review|candidate|supplement", study_id), study_id)
        self.assertFalse(ids & set(self.data["aliases"]))
        self.assertFalse(self.sources & OWNER_REMOVALS)
        self.assertEqual(len(self.data["aliases"]), 104)
        contract = json.loads(HISTORICAL_ROUTES.read_text())
        self.assertFalse(self.sources & OWNER_REMOVALS)
        self.assertEqual(hashlib.sha256("\n".join(sorted(self.sources)).encode()).hexdigest(), contract["flag_removal_05_after_source_set_sha256"])

    def test_every_frozen_historical_ordinal_and_default_keeps_its_source(self):
        contract = json.loads(HISTORICAL_ROUTES.read_text())
        old_contract_counts = contract["canonical_ordinals"]
        before = contract["pr44_beforeimage"]
        self.assertEqual(contract["baseline_commit"], "42c2aebc28dfe450b8a5f93494af04084b0935e7")
        self.assertEqual(before["baseline_commit"], "dfb21bfc42764334fedab13ece301862d878e587")
        self.assertEqual(len(old_contract_counts), 28)
        self.assertEqual(len(before["canonical_bindings"]), 25)
        self.assertEqual(len(before["alias_bindings"]), before["alias_count"])
        self.assertEqual(before["alias_count"], 103)
        self.assertEqual(len(set(before["alias_bindings"]) - set(old_contract_counts)), contract["legacy_alias_count"])

        old_canonical = before["canonical_bindings"]
        old_aliases = before["alias_bindings"]
        before_bindings = {"canonical": old_canonical, "aliases": old_aliases}
        self.assertEqual(hashlib.sha256(json.dumps(before_bindings, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), before["source_bindings_sha256"])
        historic_canonical = {sid: old_canonical.get(sid, old_aliases.get(sid)) for sid in old_contract_counts}
        historic_aliases = {sid: old_aliases[sid] for sid in sorted(set(old_aliases) - set(old_contract_counts))}
        historic_payload = {"canonical": historic_canonical, "aliases": historic_aliases}
        self.assertEqual(hashlib.sha256(json.dumps(historic_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), contract["historical_source_bindings_sha256"])
        removed = set(before["removed_sources_for_this_change"])
        self.assertEqual(removed, OWNER_REMOVALS - {
            "/outside/assets/owner-review/core-trips/C538",
            "/outside/assets/owner-review/core-trips/C542",
            "/outside/assets/owner-review/core-trips/C941",
            "/outside/hoover-dam/005",
            "/outside/study-0726/006",
        })

        def route_source(route):
            if not isinstance(route, dict):
                return None
            study = self.studies.get(route.get("studyId"))
            index = route.get("index")
            if study is None or not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(study["images"]):
                return None
            return study["images"][index]["src"]

        def alias_bindings(alias_id):
            alias = self.data["aliases"][alias_id]
            if isinstance(alias.get("targets"), list):
                targets = [route_source(route) for route in alias["targets"]]
                default_target = alias.get("defaultTarget") if "defaultTarget" in alias else next((route for route in alias["targets"] if route is not None), None)
                return {"default": route_source(default_target), "targets": targets}
            target_study = self.studies.get(alias.get("studyId"))
            indices = alias.get("indices", [])
            targets = [target_study["images"][index]["src"] if target_study and isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(target_study["images"]) else None for index in indices]
            default_index = alias.get("defaultIndex")
            if default_index is None:
                default_index = next((index for index in indices if isinstance(index, int) and not isinstance(index, bool) and index >= 0), None)
            default = target_study["images"][default_index]["src"] if target_study and isinstance(default_index, int) and not isinstance(default_index, bool) and 0 <= default_index < len(target_study["images"]) else None
            return {"default": default, "targets": targets}

        self.assertEqual(set(self.data["aliases"]), set(old_aliases) | {"montreal-august-2023-gallery"})
        self.assertEqual(len(self.data["studies"]), 25)
        removed_sources = set(before["removed_sources_for_this_change"])
        for study_id, binding in old_canonical.items():
            if study_id in self.studies:
                study = self.studies[study_id]
                actual = {"default": study["images"][0]["src"] if study["images"] else None, "targets": [image["src"] for image in study["images"]]}
            else:
                self.assertIn(study_id, self.data["aliases"], study_id)
                actual = alias_bindings(study_id)
            expected = {"default": binding["default"] if binding["default"] not in removed_sources else None,
                        "targets": [src if src not in removed_sources else None for src in binding["targets"]]}
            self.assertEqual(actual, expected, study_id)
        for alias_id, binding in old_aliases.items():
            self.assertIn(alias_id, self.data["aliases"], alias_id)
            expected = {"default": binding["default"] if binding["default"] not in removed_sources else None,
                        "targets": [src if src not in removed_sources else None for src in binding["targets"]]}
            self.assertEqual(alias_bindings(alias_id), expected, alias_id)
        current = self.studies["montreal-august-2023-photos"]
        self.assertEqual(len(current["images"]), 15)
        self.assertEqual([image["src"] for image in current["images"]], [src for src in old_canonical["montreal-august-2023-gallery"]["targets"] if src not in removed_sources])
        self.assertEqual(self.data["aliases"]["marlborough-2025-may"], {"targets": [None], "defaultTarget": None})

    def test_public_copy_is_clean_and_genuine_uncertainty_is_preserved(self):
        forbidden = re.compile(r"archived state label|metadata (?:review|cluster)|unsorted review|review supplement|location pending", re.I)
        for study in self.data["studies"]:
            public = " ".join([study.get("place", ""), study.get("region", ""), study.get("country", "")])
            self.assertIsNone(forbidden.search(public), f"{study['id']}: {public}")
        self.assertEqual(self.studies["thailand-2026-july"]["status"], "PENDING")
        self.assertEqual(self.studies["thailand-2026-july"]["region"], "Location unconfirmed")
        self.assertEqual(self.studies["celebration-2025-september"]["status"], "PENDING")
        self.assertNotIn("marlborough-2025-may", self.studies)
        self.assertEqual(self.studies["cruise-2024-december"]["status"], "PENDING")
        self.assertEqual(self.studies["montreal-august-2023-photos"]["status"], "PRELIM")
        self.assertEqual(self.studies["maryland-national-harbor-2023-august"]["status"], "PRELIM")

    def test_approved_vegas_and_atlanta_groups_are_chronological_and_source_bound(self):
        vegas = self.studies["las-vegas-2025-june-gallery"]
        self.assertEqual((vegas["date"], vegas["dateEnd"], len(vegas["images"]), vegas["status"]), ("2025-06-14", "2025-06-14", 17, "PENDING"))
        vegas_sources = [image["src"] for image in vegas["images"]]
        resort_sources = [
            "/outside/assets/owner-review/additional-trips/A484",
            "/outside/assets/owner-review/additional-trips/A488",
            "/outside/assets/owner-review/additional-trips/A502",
            "/outside/assets/owner-review/additional-trips/A504",
        ]
        self.assertEqual([image["t"] for image in vegas["images"]], sorted(image["t"] for image in vegas["images"]))
        self.assertEqual([vegas_sources.index(source) for source in resort_sources], sorted(vegas_sources.index(source) for source in resort_sources))
        self.assertEqual(vegas["series"][0]["title"], "Resort interiors & displays")

        atlanta = self.studies["atlanta-2025-june"]
        self.assertEqual((atlanta["place"], atlanta["region"], atlanta["country"], atlanta["status"]), ("Atlanta", "Georgia", "United States", "PENDING"))
        self.assertEqual((atlanta["date"], atlanta["dateEnd"], len(atlanta["images"])), ("2025-06-18", "2025-06-18", 32))
        self.assertEqual([(series["start"], series["count"], series["title"]) for series in atlanta["series"]], [(0, 7, "Fountains & gardens"), (7, 4, "Downtown Atlanta"), (11, 21, "Aquarium & marine life")])

        aquarium_sources = [
            "/outside/assets/owner-review/additional-trips/" + source
            for source in ("A404", "A408", "A410", "A412", "A414", "A416", "A418", "A420", "A422", "A426", "A428", "A430", "A432", "A434", "A440", "A443", "A449", "A451")
        ]
        def alias_sources(alias_id):
            return [self.studies[target["studyId"]]["images"][target["index"]]["src"] for target in self.data["aliases"][alias_id]["targets"]]

        self.assertEqual(alias_sources("resort-scenes-2025-june"), resort_sources)
        self.assertEqual(alias_sources("aquarium-scenes-2025-june"), aquarium_sources)
        unsorted_sources = alias_sources("unsorted-review")
        self.assertEqual(len(unsorted_sources), 23)
        self.assertEqual(unsorted_sources[1:5], resort_sources)
        self.assertEqual(unsorted_sources[5:], aquarium_sources)

    def test_finalized_august_source_map_moves_without_inventing_gps_or_dropping_sources(self):
        montreal = self.studies["montreal-august-2023-photos"]
        self.assertEqual((montreal["place"], montreal["region"], montreal["country"], montreal["status"]), ("Montréal", "Québec", "Canada", "PRELIM"))
        self.assertEqual((montreal["date"], montreal["dateEnd"], len(montreal["images"])), ("2023-08-06", "2023-08-08", 15))
        self.assertEqual(sum(not image.get("d") for image in montreal["images"]), 1)
        self.assertEqual([image["src"] for image in montreal["images"][10:12]], [
            "/outside/assets/montreal-august-2023/ma23-53861ee23544db00989e",
            "/outside/assets/montreal-august-2023/ma23-f795961661e9518e2029",
        ])
        maryland = self.studies["maryland-national-harbor-2023-august"]
        self.assertEqual((maryland["place"], maryland["region"], maryland["country"], maryland["status"], maryland["date"]), ("National Harbor", "Maryland", "United States", "PRELIM", "2023-08-13"))
        self.assertEqual(len(maryland["images"]), 1)
        self.assertEqual(maryland["images"][0]["src"], "/outside/assets/montreal-august-2023/ma23-e4c5925d3331b3e15c75")
        self.assertNotIn("lat", maryland["images"][0])
        self.assertNotIn("lon", maryland["images"][0])

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
        self.assertEqual(self.studies["australia-2026-july-photos"]["series"][0]["title"], "Busselton Jetty")
        self.assertEqual(self.studies["thailand-2026-july"]["series"][0]["title"], "Gilded shrine & garden")
        self.assertEqual(self.studies["cruise-2024-december"]["series"][1]["title"], "Ship & open water")
        self.assertEqual(self.studies["montreal-august-2023-photos"]["series"][2]["title"], "Garden paths")
        europe = self.studies["europe-shared-album"]
        self.assertEqual((europe["date"], europe["dateEnd"]), ("", ""))
        self.assertEqual(sum(not image.get("d") for image in europe["images"]), 17)
        self.assertEqual((europe["series"][0]["date"], europe["series"][1]["date"]), ("2023-02-19", ""))

    def test_worklist_uses_full_end_and_start_dates_in_descending_order(self):
        order = [s["id"] for s in self.data["studies"]]
        sorted_ids = [s["id"] for s in sorted(self.data["studies"], key=lambda s: (s.get("dateEnd") or s.get("date") or "", s.get("date") or ""), reverse=True)]
        self.assertEqual(order, sorted_ids)
        self.assertLess(order.index("maryland-national-harbor-2023-august"), order.index("montreal-august-2023-photos"))
        self.assertLess(order.index("montreal-august-2023-photos"), order.index("philadelphia-2023-spring"))
        self.assertLess(order.index("albania-2026-june"), order.index("rome-vatican-2026-june"))

    def test_november_montreal_supplement_is_additive_and_has_priority_source(self):
        study = self.studies["montreal-november-2025-photos"]
        self.assertEqual(len(study["images"]), 18)
        sources = [image["src"] for image in study["images"]]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertTrue(any("50687dc46ae34c23be92b217abb3de9f" in source for source in sources))
        self.assertEqual(sum("/montreal-november-album-gap/" in source for source in sources), 11)
        self.assertEqual([series["date"] for series in study["series"]], ["2025-11-27", "2025-11-28", "2025-11-29", "2025-11-30"])
        self.assertEqual([series["count"] for series in study["series"]], [1, 5, 11, 1])
        self.assertEqual(study["status"], "PENDING")
        self.assertEqual((study["date"], study["dateEnd"]), ("2025-11-27", "2025-11-30"))

    def test_owner_approved_utah_night_sky_photo_is_added_once_and_chronological(self):
        study = self.studies["american-southwest-2025-october-photos"]
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
