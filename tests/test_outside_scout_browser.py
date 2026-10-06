import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
ROOT = Path(__file__).parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/outside-pr45-source-route-baseline.json").read_text())
PR_ROUTE_BASELINE = json.loads((ROOT / "tests/fixtures/outside-puerto-rico-prechange-routes.json").read_text())
NEW_DUPLICATE_REMOVALS = set(PR_ROUTE_BASELINE["removed_sources"]) | {
    "/outside/assets/owner-review/galapagos/G208",
    "/outside/assets/owner-review/core-trips/C219",
    "/outside/assets/owner-review/core-trips/C351",
    "/outside/assets/owner-review/core-trips/C484",
    "/outside/assets/owner-review/additional-trips/A460",
    "/outside/assets/owner-review/additional-trips/A508",
    "/outside/assets/owner-review/additional-trips/A505",
    "/outside/assets/owner-review/additional-trips/A514",
}
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
EVIDENCE_DIR = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-scout-browser"))
SCOUTS = [
    {"id": "pakistan-2026-summer-gallery-20261005", "old_id": "pakistan-2026-summer-photos", "date": "2026-06-24", "end": "2026-06-25", "study_date": "2026-06-28", "study_end": "2026-07-05", "total": 30, "source": "/outside/assets/summer-2026/0005", "default_source": "/outside/assets/owner-review/summer-2026/S0102", "place": "Karachi", "transit_place": "Rome"},
    {"id": "australia-2026-july-gallery-20261005-quokka", "old_id": "australia-2026-july-photos", "date": "2026-07-06", "end": "2026-07-06", "study_date": "2026-07-07", "study_end": "2026-07-16", "total": 33, "source": "/outside/assets/owner-review/additional-trips/A278", "default_source": "/outside/assets/summer-2026/0404", "place": "Busselton", "transit_place": "Bangkok"},
    {"id": "cruise-2024-december-gallery", "old_id": "cruise-2024-december", "date": "2024-12-17", "end": "2024-12-17", "study_date": "2024-12-15", "study_end": "2024-12-20", "total": 8, "source": "/outside/assets/owner-review/additional-trips/A306", "place": None, "transit_place": "Merritt Island"},
]


class OutsideScoutBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "webkit")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    @staticmethod
    def image_src(page):
        src = page.locator("[data-cells] img").first.get_attribute("src") or ""
        return re.sub(r"-(?:s|m|l)\.webp$", "", src)

    def test_scout_caption_dates_worklist_and_primary_paint_on_desktop_and_mobile(self):
        expected_top_three = ["new-zealand-2026-july-photos-161007", SCOUTS[1]["id"], SCOUTS[0]["id"]]
        for width, height, viewport_name in ((1440, 1000, "desktop"), (375, 812, "mobile")):
            for spec in SCOUTS:
                with self.subTest(viewport=viewport_name, scout=spec["id"]):
                    context = self.browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    # Bare canonical study hash is the intentional SE1 default.
                    page.goto(urljoin(BASE_URL, f"#{spec['id']}"), wait_until="domcontentloaded")
                    page.wait_for_function("document.querySelectorAll('[data-series] [data-se]').length > 0", timeout=10000)
                    payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                    self.assertEqual([study["id"] for study in payload["studies"][:3]], expected_top_three)
                    study = next(item for item in payload["studies"] if item["id"] == spec["id"])
                    self.assertEqual((study["date"], study["dateEnd"]), (spec["study_date"], spec["study_end"]))
                    self.assertEqual(len(study["images"]), spec["total"])
                    chapters = sorted(study["series"], key=lambda item: item["start"])
                    display_numbers = [chapter["displayNumber"] for chapter in chapters]
                    self.assertEqual(display_numbers, list(range(len(chapters))))
                    scout_series = next(chapter for chapter in chapters if chapter["displayNumber"] == 0)
                    scout_images = study["images"][scout_series["start"]:scout_series["start"] + scout_series["count"]]
                    self.assertTrue(scout_images)
                    self.assertTrue(all(image["transit"] for image in scout_images))
                    self.assertEqual(scout_images[0]["src"], spec["source"])
                    self.assertEqual((scout_series["date"], scout_series["dateEnd"]), (spec["date"], spec["end"]))
                    default_series = next(chapter for chapter in chapters if chapter["displayNumber"] == 1)
                    default_source = study["images"][default_series["start"]]["src"]
                    if spec.get("default_source"):
                        self.assertEqual(default_source, spec["default_source"])
                    default_place = study["images"][default_series["start"]]["place"]
                    if spec.get("place"):
                        self.assertEqual(default_place, spec["place"])
                    self.assertFalse(study["images"][default_series["start"]]["transit"])

                    rows = page.locator(".oz-rows [data-study]")
                    visible_ids = [row.get_attribute("href").lstrip("#") for row in rows.all()]
                    if spec["id"] == "cruise-2024-december-gallery":
                        self.assertEqual(rows.locator(f'[href="#{spec["id"]}"]').count(), 0)
                    else:
                        self.assertIn(spec["id"], visible_ids)
                        row = page.locator(f'.oz-row[href="#{spec["id"]}"]')
                        expected_row_date = f"{spec['study_date']} to {spec['study_end'][5:]}" if spec["study_date"][:4] == spec["study_end"][:4] else f"{spec['study_date']} to {spec['study_end']}"
                        self.assertIn(expected_row_date, row.get_attribute("aria-label"))

                    self.assertEqual((len(visible_ids), 233), (6, 233))
                    self.assertIn("6 studies", page.locator(".oz-topmeta").inner_text().lower())
                    self.assertIn("233 images", page.locator(".oz-topmeta").inner_text().lower())
                    buttons = page.locator("[data-series] [data-se]")
                    self.assertEqual(buttons.count(), len(chapters))
                    active_position = chapters.index(default_series)
                    for position, chapter in enumerate(chapters):
                        display_number = chapter["displayNumber"]
                        chapter_images = study["images"][chapter["start"]:chapter["start"] + chapter["count"]]
                        if display_number == 0:
                            places = list(dict.fromkeys(image["place"] for image in chapter_images if image["transit"] and image.get("place")))
                            chapter_name = f"Scout · {', '.join(places)}" if places else "Scout"
                        else:
                            places = list(dict.fromkeys(image["place"] for image in chapter_images if not image["transit"] and image.get("place")))
                            chapter_name = " · ".join(places) or "Location unconfirmed"
                        self.assertEqual(buttons.nth(position).get_attribute("data-se"), str(position))
                        self.assertEqual(buttons.nth(position).locator(".oz-se-cap b").inner_text().upper(), f"SE {display_number} · {chapter_name}".upper())
                        aria = buttons.nth(position).get_attribute("aria-label")
                        self.assertTrue(aria.startswith(f"Series {display_number}, {chapter_name},"), aria)
                        self.assertIn(f"{chapter['count']} images", aria)
                    self.assertEqual(buttons.nth(active_position).get_attribute("aria-current"), "true")
                    self.assertIn(f"SE 1/{len(chapters)}", page.locator('[data-ov="tr"]').inner_text())
                    self.assertEqual(self.image_src(page), default_source)
                    tl_text = page.locator('[data-ov="tl"]').inner_text().upper()
                    if spec.get("place"):
                        self.assertIn(spec["place"].upper(), tl_text)
                    self.assertNotIn("TRANSIT", tl_text)
                    if spec["id"] == "pakistan-2026-summer-gallery-20261005":
                        self.assertEqual(page.locator(".oz-journey").count(), 0)
                    page.wait_for_function("expected => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && im.currentSrc.includes(expected); }", arg=default_source, timeout=15000)
                    visible_image = page.locator("[data-cells] img").first
                    self.assertTrue(visible_image.is_visible())
                    self.assertGreater(visible_image.evaluate("im => im.naturalWidth"), 0)
                    self.assertTrue(visible_image.evaluate("(im, stem) => im.dataset.want.replace(/-(?:s|m|l)\\.webp$/, '') === stem", default_source))
                    page.locator("[data-viewport]").screenshot(path=str(EVIDENCE_DIR / f"{viewport_name}-{spec['id']}-se1-primary.png"))

                    # PageUp exposes transit SE0, its exact source, place, and SCOUT badge.
                    page.keyboard.press("PageUp")
                    page.wait_for_function("() => document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '0'")
                    page.wait_for_function("() => document.querySelector('[data-live]')?.textContent.includes('Series 0.')")
                    self.assertIn("SE 0/", page.locator('[data-ov="tr"]').inner_text())
                    self.assertEqual(self.image_src(page), spec["source"])
                    transit_overlay = page.locator('[data-ov="tl"]').inner_text().upper()
                    self.assertIn(spec["transit_place"].upper(), transit_overlay)
                    self.assertIn("TRANSIT", transit_overlay)
                    self.assertIn("SCOUT", page.locator('[data-ov="br"]').inner_text().upper())
                    self.assertEqual(page.locator('[data-series] [aria-current="true"]').locator(".oz-se-cap b").inner_text().upper().split(" · ", 1)[0], "SE 0")
                    self.assertTrue(page.locator("[data-cells] img").first.evaluate("(im, stem) => im.dataset.want.replace(/-(?:s|m|l)\\.webp$/, '') === stem", spec["source"]))
                    page.keyboard.press("PageDown")
                    page.wait_for_function("() => document.querySelector('[data-series] [aria-current=true]')?.dataset.se === String([...document.querySelectorAll('[data-series] [data-se]')].findIndex(b=>b.textContent.includes('SE 1')))")
                    self.assertEqual(self.image_src(page), default_source)

                    # Bare legacy aliases also default to the first SE1 image; /1 remains source-bound.
                    for route_id in (spec["id"], spec["old_id"]):
                        page.goto(urljoin(BASE_URL, f"#{route_id}"), wait_until="domcontentloaded")
                        page.wait_for_function("expected => { const want=document.querySelector('[data-cells] img')?.dataset.want || ''; return want.replace(/-(?:s|m|l)\\.webp$/, '') === expected; }", arg=default_source, timeout=10000)
                        self.assertEqual(self.image_src(page), default_source, route_id)
                        ordinal_source = spec["source"]
                        if route_id == spec["old_id"]:
                            alias = payload["aliases"][route_id]
                            target = alias["targets"][0] if isinstance(alias.get("targets"), list) and alias["targets"] else None
                            target_study = next((item for item in payload["studies"] if isinstance(target, dict) and item["id"] == target.get("studyId")), None)
                            target_index = target.get("index") if isinstance(target, dict) else None
                            ordinal_source = target_study["images"][target_index]["src"] if target_study and isinstance(target_index, int) and not isinstance(target_index, bool) and 0 <= target_index < len(target_study["images"]) else None
                        self.assertIsNotNone(ordinal_source)
                        page.goto(urljoin(BASE_URL, f"#{route_id}/1"), wait_until="domcontentloaded")
                        page.wait_for_function("expected => { const want=document.querySelector('[data-cells] img')?.dataset.want || ''; return want.replace(/-(?:s|m|l)\\.webp$/, '') === expected; }", arg=ordinal_source, timeout=10000)
                        self.assertEqual(self.image_src(page), ordinal_source, f"{route_id}/1")

                    # Review/export still keys on the exact selected image source.
                    page.goto(urljoin(BASE_URL, f"#{spec['id']}"), wait_until="domcontentloaded")
                    page.wait_for_function("expected => { const want=document.querySelector('[data-cells] img')?.dataset.want || ''; return want.replace(/-(?:s|m|l)\\.webp$/, '') === expected; }", arg=default_source, timeout=10000)
                    page.locator("[data-review-flag]").click()
                    saved = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
                    self.assertEqual(saved["flaggedSrcs"], [default_source])
                    with page.expect_download(timeout=5000) as download_info:
                        page.locator("[data-review-export]").click()
                    exported = json.loads(Path(download_info.value.path()).read_text())
                    self.assertEqual(exported["flagged"][0]["src"], default_source)
                    self.assertEqual(exported["flagged"][0]["date"], f"{spec['study_date']} to {spec['study_end'][5:]}")
                    self.assertEqual(exported["flagged"][0]["reference"], spec["id"])
                    self.assertEqual(errors, [], errors)
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                    context.close()

    def test_duplicate_oneplus_camera_name_is_normalized_only_in_overlay(self):
        study = next(item for item in DATA["studies"] if any(image["src"] == "/outside/assets/summer-2026/1035" for image in item["images"]))
        records = [next(item for item in study["images"] if item["src"] == source) for source in (
            "/outside/assets/summer-2026/1035",
            "/outside/assets/owner-review/summer-2026/S1041",
        )]
        self.assertEqual([record["cam"] for record in records], ["OnePlus 11 5G", "OnePlus OnePlus 11 5G"])
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        for ordinal, record in enumerate(records, 1):
            page.goto(urljoin(BASE_URL, f"#new-zealand-2026-july-photos/{ordinal}"), wait_until="domcontentloaded")
            page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && (im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", arg=record["src"], timeout=15000)
            overlay = page.locator('[data-ov="bl"]').inner_text()
            self.assertIn("ONEPLUS 11 5G", overlay)
            self.assertNotIn("ONEPLUS ONEPLUS", overlay)
            self.assertIn(record["ex"], overlay)
            self.assertIn(record["d"], page.locator('[data-ov="tr"]').inner_text())
            image = page.locator("[data-cells] img").first
            self.assertTrue(image.evaluate("(im, stem) => im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')", record["src"]))
        controls = {
            "OnePlus CPH2451": "ONEPLUS 11 5G",
            "Apple iPhone 15": "APPLE IPHONE 15",
            "Apple iPhone 12 Pro Max": "APPLE IPHONE 12 PRO MAX",
            "HTC One M9": "HTC ONE M9",
            "": None,
        }
        for raw_camera, expected in controls.items():
            study, index, record = next((item, index, image) for item in DATA["studies"] for index, image in enumerate(item["images"]) if image["cam"] == raw_camera)
            page.goto(urljoin(BASE_URL, f"#{study['id']}/{index + 1}"), wait_until="domcontentloaded")
            page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && (im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", arg=record["src"], timeout=15000)
            lines = page.locator('[data-ov="bl"]').inner_text().splitlines()
            if expected:
                self.assertEqual(lines[-1], expected)
            else:
                self.assertEqual(lines, [value.upper() for value in (record["ex"], record["fl"]) if value])
        context.close()

    def test_all_2305_frozen_public_links_keep_source_and_exact_tombstones(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        page.route("**/*.webp", lambda route: route.abort())
        page.goto(BASE_URL, wait_until="domcontentloaded")
        OWNER_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005.json").read_text())
        LATEST_FLAGS = json.loads((ROOT / "tests/fixtures/outside-owner-photo-removals-20261005-161007.json").read_text())
        pending = set(FIXTURE["pending_removal_sources"]) | NEW_DUPLICATE_REMOVALS | set(OWNER_FLAGS["flagged_sources"]) | set(LATEST_FLAGS["newly_flagged_sources"])
        restore_src = FIXTURE["authorized_restore_source"]["src"]
        restored = set(FIXTURE["allowed_restored_routes"])
        payload = json.loads(page.locator("#oz-data").text_content() or "{}")

        def first_se1(source):
            for study in payload["studies"]:
                if any(image["src"] == source for image in study["images"]):
                    return next((image["src"] for image in study["images"] if image.get("se") == 1), None)
            return None

        cases = []
        for route in FIXTURE["routes"]:
            route_hash, source = route["hash"], route["source"]
            if route_hash in restored:
                source = restore_src if re.search(r"/[1-9]\d*$", route_hash) else first_se1(restore_src)
            elif source in pending:
                source = None
            elif source is not None and not re.search(r"/[1-9]\d*$", route_hash):
                source = first_se1(source)
            cases.append({"hash": route_hash, "expected": source})
        outcome = page.evaluate("""cases => {
          const failures = [];
          const routeError = document.querySelector('[data-route-error]');
          for (const item of cases) {
            location.hash = item.hash;
            window.dispatchEvent(new PopStateEvent('popstate'));
            const unavailable = !routeError.hidden;
            const image = document.querySelector('[data-cells] img');
            const actual = (image?.dataset.want || '').replace(/-(?:s|m|l)\\.webp$/, '');
            const passed = item.expected === null ? unavailable : (!unavailable && actual === item.expected);
            if (!passed && failures.length < 8) failures.push({hash:item.hash, expected:item.expected, actual, unavailable});
          }
          return {checked:cases.length, failures};
        }""", cases)
        context.close()
        self.assertEqual(outcome["checked"], 2305)
        self.assertEqual(outcome["failures"], [], outcome)


if __name__ == "__main__":
    unittest.main()
