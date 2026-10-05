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
    {"id": "pakistan-2026-summer-gallery-20261005", "old_id": "pakistan-2026-summer-photos", "title": "SE 0 · SCOUT · Rome, Tirana", "series_title": "SCOUT · Rome, Tirana", "date": "2026-06-24", "end": "2026-06-25", "study_date": "2026-06-28", "study_end": "2026-07-05", "count": 11, "total": 30, "series": 7, "source": "/outside/assets/summer-2026/0005", "next_source": "/outside/assets/owner-review/summer-2026/S0102"},
    {"id": "australia-2026-july-gallery-20261005", "old_id": "australia-2026-july-photos", "title": "SE 0 · SCOUT · Bangkok", "series_title": "SCOUT · Bangkok", "date": "2026-07-06", "end": "2026-07-06", "study_date": "2026-07-07", "study_end": "2026-07-16", "count": 1, "total": 33, "series": 8, "source": "/outside/assets/owner-review/additional-trips/A278"},
    {"id": "cruise-2024-december-gallery", "old_id": "cruise-2024-december", "title": "SE 0 · SCOUT · Merritt Island", "series_title": "SCOUT · Merritt Island", "date": "2024-12-17", "end": "2024-12-17", "study_date": "2024-12-15", "study_end": "2024-12-20", "count": 1, "total": 8, "series": 6, "source": "/outside/assets/owner-review/additional-trips/A306"},
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

    def test_scout_caption_dates_worklist_and_primary_paint_on_desktop_and_mobile(self):
        expected_top_three = ["new-zealand-2026-july-photos", SCOUTS[1]["id"], SCOUTS[0]["id"]]
        for width, height, viewport_name in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            for spec in SCOUTS:
                with self.subTest(viewport=viewport_name, scout=spec["id"]):
                    context = self.browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(urljoin(BASE_URL, f"#{spec['id']}/1"), wait_until="domcontentloaded")
                    page.wait_for_function("document.querySelectorAll('[data-series] [data-se]').length > 0", timeout=10000)
                    payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                    self.assertEqual([study["id"] for study in payload["studies"][:3]], expected_top_three)
                    study = next(item for item in payload["studies"] if item["id"] == spec["id"])
                    self.assertEqual((study["date"], study["dateEnd"]), (spec["study_date"], spec["study_end"]))
                    self.assertEqual((len(study["images"]), len(study["series"])), (spec["total"], spec["series"]))
                    self.assertEqual(study["images"][0]["src"], spec["source"])
                    scout_row = page.locator(f'.oz-row[href="#{spec["id"]}"]')
                    if spec["id"] == "cruise-2024-december-gallery":
                        # Historical routes still resolve, but pre-cutoff collections are not recent worklist rows.
                        self.assertEqual(scout_row.count(), 0)
                    else:
                        self.assertEqual(scout_row.get_attribute("aria-label").split(", ")[1], f"{spec['study_date']} to {spec['study_end'][5:]}" if spec["study_date"][:4] == spec["study_end"][:4] else f"{spec['study_date']} to {spec['study_end']}")
                    buttons = page.locator("[data-series] [data-se]")
                    self.assertEqual(buttons.count(), spec["series"])
                    for position, chapter in enumerate(sorted(study["series"], key=lambda item: item["start"])):
                        visible_number = chapter.get("displayNumber", position + 1)
                        visible_title = chapter.get("title") or f"Series {visible_number}"
                        self.assertEqual(buttons.nth(position).get_attribute("data-se"), str(position))
                        self.assertEqual(buttons.nth(position).locator(".oz-se-cap b").inner_text(), f"SE {visible_number} · {visible_title}")
                        self.assertTrue(buttons.nth(position).get_attribute("aria-label").startswith(f"Series {visible_number}, {visible_title},"))
                    self.assertEqual(buttons.nth(0).get_attribute("data-se"), "0")
                    self.assertEqual(buttons.nth(0).locator(".oz-se-cap b").inner_text(), spec["title"])
                    self.assertIn("Series 0, " + spec["series_title"], buttons.nth(0).get_attribute("aria-label"))
                    self.assertIn(spec["date"], buttons.nth(0).get_attribute("aria-label"))
                    self.assertIn(spec["count"] and f"{spec['count']} images", buttons.nth(0).get_attribute("aria-label"))
                    self.assertEqual(buttons.nth(0).get_attribute("aria-current"), "true")
                    self.assertIn(f"SE 0/{spec['series']}", page.locator('[data-ov="tr"]').inner_text())
                    self.assertFalse(spec["id"] == "pakistan-2026-summer-gallery-20261005" and page.locator(".oz-journey").count() > 0)

                    page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && im.currentSrc.includes(stem) && /-(s|m|l)\\.webp$/.test(im.currentSrc); }", arg=spec["source"], timeout=15000)
                    visible_image = page.locator("[data-cells] img").first
                    self.assertTrue(visible_image.is_visible())
                    self.assertGreater(visible_image.evaluate("im => im.naturalWidth"), 0)
                    self.assertTrue(visible_image.evaluate("(im, stem) => im.currentSrc.includes(stem)" , spec["source"]))
                    if spec["id"] == "pakistan-2026-summer-gallery-20261005":
                        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE_DIR / f"{viewport_name}-scout-primary.png"))
                        page.keyboard.press("PageDown")
                        page.wait_for_function("() => document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '1'")
                        page.wait_for_function("() => document.querySelector('[data-live]')?.textContent.includes('Series 1.')")
                        self.assertIn("Gardens & heritage", page.locator('[data-series] [aria-current="true"]').inner_text())
                        self.assertIn("SE 1/7", page.locator('[data-ov="tr"]').inner_text())
                        self.assertTrue(page.locator("[data-cells] img").first.evaluate("(im, stem) => im.dataset.want.startsWith(stem)", spec["next_source"]))
                        page.keyboard.press("PageUp")
                        page.wait_for_function("() => document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '0'")
                        page.wait_for_function("() => document.querySelector('[data-live]')?.textContent.includes('Series 0.')")
                        self.assertIn("SE 0/7", page.locator('[data-ov="tr"]').inner_text())
                        self.assertTrue(page.locator("[data-cells] img").first.evaluate("(im, stem) => im.dataset.want.startsWith(stem)", spec["source"]))
                        page.locator("[data-review-flag]").click()
                        saved = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
                        self.assertEqual(saved["flaggedSrcs"], [spec["source"]])
                        with page.expect_download(timeout=5000) as download_info:
                            page.locator("[data-review-export]").click()
                        exported = json.loads(Path(download_info.value.path()).read_text())
                        self.assertEqual(exported["flagged"][0]["src"], spec["source"])
                        self.assertEqual(exported["flagged"][0]["date"], "2026-06-28 to 07-05")
                        self.assertEqual(exported["flagged"][0]["reference"], spec["id"])
                    self.assertEqual(errors, [], errors)
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                    context.close()

    def test_duplicate_oneplus_camera_name_is_normalized_only_in_overlay(self):
        study = next(item for item in DATA["studies"] if item["id"] == "new-zealand-2026-july-photos")
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
        pending = set(FIXTURE["pending_removal_sources"]) | NEW_DUPLICATE_REMOVALS | set(OWNER_FLAGS["flagged_sources"])
        restore_src = FIXTURE["authorized_restore_source"]["src"]
        restored = set(FIXTURE["allowed_restored_routes"])
        cases = [{"hash": route["hash"], "expected": restore_src if route["hash"] in restored else (None if route["source"] in pending else route["source"])} for route in FIXTURE["routes"]]
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
