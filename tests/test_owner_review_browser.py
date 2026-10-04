import json
import os
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
CANONICAL_PAKISTAN = "pakistan-2026-summer-gallery"


class OutsideOwnerReviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    @staticmethod
    def payload(page):
        return json.loads(page.locator("#oz-data").text_content() or "{}")

    @staticmethod
    def target_source(payload, target):
        if not target:
            return None
        study = next((item for item in payload["studies"] if item["id"] == target.get("studyId")), None)
        index = target.get("index")
        if study is None or not isinstance(index, int) or not 0 <= index < len(study["images"]):
            return None
        return study["images"][index]["src"]

    @classmethod
    def route_source(cls, payload, route_id, ordinal=None):
        study = next((item for item in payload["studies"] if item["id"] == route_id), None)
        if study is not None:
            index = min(max((ordinal or 1) - 1, 0), len(study["images"]) - 1)
            return study["images"][index]["src"]
        alias = payload["aliases"].get(route_id)
        if not alias:
            return None
        if "targets" not in alias:
            study = next((item for item in payload["studies"] if item["id"] == alias.get("studyId")), None)
            index = alias.get("defaultIndex", -1) if ordinal is None else (alias.get("indices", [])[ordinal - 1] if 1 <= ordinal <= len(alias.get("indices", [])) else None)
            return study["images"][index]["src"] if study and isinstance(index, int) and 0 <= index < len(study["images"]) else None
        if ordinal is None:
            return cls.target_source(payload, alias.get("defaultTarget"))
        targets = alias.get("targets", [])
        return cls.target_source(payload, targets[ordinal - 1]) if 1 <= ordinal <= len(targets) else None

    @staticmethod
    def displayed_date(study):
        start, end = study.get("date", ""), study.get("dateEnd", "")
        if not start:
            return end
        if not end or end == start:
            return start
        if len(start) == len(end) == 10 and start[:4] == end[:4] and end >= start:
            return f"{start} to {end[5:]}"
        return f"{start} to {end}"

    def test_reader_exposes_owner_review_controls(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        self.assertTrue(page.locator("[data-review-flag]").is_visible(), "active-photo flag control is missing")
        self.assertTrue(page.locator("[data-review-count]").is_visible(), "flag count is missing")
        self.assertTrue(page.locator("[data-review-export]").is_visible(), "flag export control is missing")
        self.assertIn("does not change the published gallery", page.locator("[data-review-saved]").get_attribute("title") or "")
        context.close()

    def test_flagging_current_photo_updates_state_and_exact_source_count(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        expected_src = self.route_source(self.payload(page), CANONICAL_PAKISTAN, 1)
        page.locator("[data-review-flag]").click()
        self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
        self.assertEqual(page.locator("[data-review-flag]").inner_text(), "Unflag")
        self.assertEqual(page.locator("[data-review-count]").inner_text(), "1 flagged")
        stored = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
        self.assertEqual(stored["flaggedSrcs"], [expected_src])
        context.close()

    def test_unknown_saved_source_flags_survive_updates(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.add_init_script("localStorage.setItem('outside-studies:photo-review:v1', JSON.stringify({schema:'outside-photo-review/v1', flaggedSrcs:['legacy-source://not-in-gallery']}))")
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        self.assertEqual(page.locator("[data-review-count]").inner_text(), "1 flagged")
        page.locator("[data-review-flag]").click()
        stored = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
        self.assertIn("legacy-source://not-in-gallery", stored["flaggedSrcs"])
        self.assertEqual(len(stored["flaggedSrcs"]), 2)
        context.close()

    def test_corrupt_or_blocked_storage_is_reported_without_breaking_flags(self):
        cases = (
            ("localStorage.setItem('outside-studies:photo-review:v1', '{broken');", "corrupt"),
            ("Object.defineProperty(window, 'localStorage', {get() { throw new DOMException('blocked', 'SecurityError'); }});", "blocked"),
        )
        for setup, label in cases:
            with self.subTest(storage=label):
                context = self.browser.new_context(viewport={"width": 390, "height": 844})
                page = context.new_page()
                page.add_init_script(setup)
                page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
                self.assertIn("unavailable", page.locator("[data-review-saved]").inner_text().lower())
                page.locator("[data-review-flag]").click()
                self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
                self.assertIn("this tab", page.locator("[data-review-saved]").inner_text().lower())
                context.close()

    def test_export_download_contains_current_source_reference_and_cross_year_safe_date(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        payload = self.payload(page)
        study = next(item for item in payload["studies"] if item["id"] == CANONICAL_PAKISTAN)
        expected = {"src": study["images"][0]["src"], "studyLabel": study["place"], "date": self.displayed_date(study), "reference": study["id"]}
        page.locator("[data-review-flag]").click()
        with page.expect_download(timeout=5000) as download_info:
            page.locator("[data-review-export]").click()
        payload = json.loads(Path(download_info.value.path()).read_text())
        self.assertEqual(payload["schema"], "outside-photo-review/v1")
        self.assertIn("T", payload["generatedAt"])
        self.assertEqual(payload["flagged"], [expected])
        self.assertFalse(any(secret in json.dumps(payload).lower() for secret in ("driveid", "latitude", "longitude", "gps")))
        context.close()

    def test_flags_survive_reload_and_two_historical_aliases_resolve_the_same_source(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(urljoin(BASE_URL, "#zion/1"), wait_until="domcontentloaded")
        expected_src = self.route_source(self.payload(page), "zion", 1)
        page.locator("[data-review-flag]").click()
        self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
        page.reload(wait_until="domcontentloaded")
        self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
        alias_page = context.new_page()
        alias_page.goto(urljoin(BASE_URL, "#american-southwest-2025/2"), wait_until="domcontentloaded")
        self.assertEqual(self.route_source(self.payload(alias_page), "american-southwest-2025", 2), expected_src)
        self.assertEqual(alias_page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
        stored = alias_page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
        self.assertIn(expected_src, stored["flaggedSrcs"])
        alias_page.locator("[data-review-flag]").click()
        self.assertEqual(alias_page.locator("[data-review-flag]").get_attribute("aria-pressed"), "false")
        self.assertEqual(alias_page.locator("[data-review-count]").inner_text(), "0 flagged")
        context.close()

    def test_new_browser_context_starts_unflagged(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "false")
        self.assertEqual(page.locator("[data-review-count]").inner_text(), "0 flagged")
        context.close()

    def test_2x2_flags_first_active_image_and_stops_cine_before_toggle(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/2"), wait_until="domcontentloaded")
        expected_src = self.route_source(self.payload(page), CANONICAL_PAKISTAN, 2)
        page.locator("button[data-layout]").click()
        self.assertEqual(page.locator("[data-cells]").get_attribute("data-layout"), "4")
        page.locator("[data-cine]").click()
        self.assertEqual(page.locator("[data-cine]").get_attribute("aria-pressed"), "true")
        page.locator("[data-review-flag]").click()
        self.assertEqual(page.locator("[data-cine]").get_attribute("aria-pressed"), "false")
        stored = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
        self.assertEqual(stored["flaggedSrcs"], [expected_src])
        context.close()

    def test_mobile_review_controls_fit_viewport_and_have_touch_targets(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{CANONICAL_PAKISTAN}/1"), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-reading')")
        metrics = page.locator(".oz-review").evaluate("""el => {
          const box = el.getBoundingClientRect();
          return {scrollWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth,
            controls: Array.from(el.querySelectorAll('button')).map(button => {
              const rect = button.getBoundingClientRect();
              return {height: rect.height, right: rect.right, parentRight: box.right};
            })};
        }""")
        self.assertLessEqual(metrics["scrollWidth"], metrics["viewportWidth"])
        self.assertTrue(all(control["height"] >= 44 for control in metrics["controls"]))
        self.assertTrue(all(control["right"] <= control["parentRight"] + 1 for control in metrics["controls"]))
        context.close()


if __name__ == "__main__":
    unittest.main()
