import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from outside_links import DATA, resolve

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
LINKS_AT_FREEZE = json.loads((Path(__file__).parent / "fixtures/outside-links-at-freeze.json").read_text())


class OutsideRoutingBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "webkit")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def open_page(self, fragment="", width=1440):
        context = self.browser.new_context(viewport={"width": width, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        page.goto(urljoin(BASE_URL, fragment), wait_until="domcontentloaded")
        page.wait_for_timeout(250)
        return context, page

    @staticmethod
    def payload(page):
        return json.loads(page.locator("#oz-data").text_content() or "{}")

    @staticmethod
    def image_src(page):
        src = page.locator("[data-cells] img").first.get_attribute("src") or ""
        return re.sub(r"-(?:s|m|l)\.webp$", "", src)

    def assert_route_matches_source(self, fragment, width=1440):
        context, page = self.open_page(fragment, width)
        expected = resolve(fragment)
        if expected is None:
            self.assertTrue(page.locator("[data-route-error]").is_visible(), fragment)
            self.assertIn("no longer available", page.locator("[data-route-error]").inner_text())
        else:
            self.assertFalse(page.locator("[data-route-error]").is_visible(), fragment)
            self.assertEqual(self.image_src(page), expected, fragment)
        context.close()

    def test_unsupported_boot_is_visible_persistent_and_never_opens_default(self):
        for width in (1440, 390):
            with self.subTest(width=width):
                context, page = self.open_page("#not-a-supported-study/1", width)
                alert = page.locator("[data-route-error]")
                self.assertTrue(alert.is_visible())
                self.assertIn("no longer available", alert.inner_text())
                self.assertEqual(page.evaluate("location.hash"), "#not-a-supported-study/1")
                self.assertIsNone(page.locator('[data-study][aria-current="true"]').first.get_attribute("data-study") if page.locator('[data-study][aria-current="true"]').count() else None)
                self.assertEqual(page.locator("[data-reader]").evaluate("el => getComputedStyle(el).visibility"), "hidden")
                page.wait_for_timeout(350)
                self.assertTrue(alert.is_visible())
                self.assertEqual(page.evaluate("location.hash"), "#not-a-supported-study/1")
                context.close()

    def test_popstate_unavailable_keeps_error_and_fragment_after_deferred_timers(self):
        context, page = self.open_page("#pakistan-2026-summer/1")
        page.evaluate("history.pushState({test: true}, '', '#not-a-supported-study/2'); window.dispatchEvent(new PopStateEvent('popstate'))")
        page.wait_for_timeout(400)
        self.assertTrue(page.locator("[data-route-error]").is_visible())
        self.assertEqual(page.evaluate("location.hash"), "#not-a-supported-study/2")
        self.assertEqual(page.locator("[data-reader]").evaluate("el => getComputedStyle(el).visibility"), "hidden")
        context.close()

    def test_retained_and_removed_historical_sources_keep_their_exact_destinations(self):
        for width in (1440, 390):
            for fragment in (
                "#zion/1",
                "#american-southwest-2025",
                "#american-southwest-2025/2",
                "#projection-american-southwest-2025",
                "#hoover-dam",
                "#hoover-dam/1",
                "#projection-american-southwest-2025/18",
            ):
                with self.subTest(width=width, route=fragment):
                    self.assert_route_matches_source(fragment, width)

    def test_invalid_alias_ordinals_are_rejected_and_new_canonical_clamp_remains(self):
        for route in ("#lahore/999", "#lahore/0", "#lahore/01", "#pakistan-2026-summer/999", "#pakistan-2026-summer-photos/999", "#projection-pakistan-2026/999", "#projection-pakistan-2026-expanded-retained-20261004/999"):
            with self.subTest(route=route):
                self.assert_route_matches_source(route)
        context, page = self.open_page("#pakistan-2026-summer-gallery-20261005/999")
        study = next(s for s in self.payload(page)["studies"] if s["id"] == "pakistan-2026-summer-gallery-20261005")
        self.assertEqual(self.image_src(page), study["images"][-1]["src"])
        context.close()

    def test_every_frozen_link_and_photo_id_link_opens_its_photo_in_the_shipped_page(self):
        cases = [{"hash": link, "expected": resolve(link)} for link in LINKS_AT_FREEZE]
        cases += [{"hash": f"#{study['id']}/{image['id']}", "expected": image["src"]} for study in DATA["studies"] for image in study["images"]]
        context, page = self.open_page()
        page.route("**/*.webp", lambda route: route.abort())
        failures, checked = [], 0
        for start in range(0, len(cases), 400):
            # Fresh page per batch keeps WebKit below its history-write rate limit.
            page.goto(urljoin(BASE_URL, ""), wait_until="domcontentloaded")
            outcome = page.evaluate("""cases => {
              const failures = [];
              for (const item of cases) {
                location.hash = item.hash;
                window.dispatchEvent(new PopStateEvent('popstate'));
                const error = !document.querySelector('[data-route-error]').hidden;
                const im = document.querySelector('[data-cells] img');
                const actual = (im?.dataset.want || '').replace(/-(?:s|m|l)\\.webp$/, '');
                const okay = item.expected === null ? error : (!error && actual === item.expected);
                if (!okay && failures.length < 8) failures.push({hash:item.hash, expected:item.expected, actual, error});
              }
              return {checked:cases.length, failures};
            }""", cases[start:start + 400])
            checked += outcome["checked"]
            failures += outcome["failures"]
        context.close()
        self.assertEqual(checked, len(cases))
        self.assertEqual(failures, [])

    def test_valid_selection_recovers_and_no_journey_heading_is_invented(self):
        for width in (1440, 390):
            context, page = self.open_page("#not-a-supported-study", width)
            page.locator('[data-study="0"]').click()
            page.wait_for_timeout(350)
            self.assertFalse(page.locator("[data-route-error]").is_visible())
            self.assertEqual(page.locator('[data-study="0"]').get_attribute("aria-current"), "true")
            self.assertEqual(page.locator(".oz-journey").count(), 0)
            context.close()

    def test_mobile_native_back_from_reader_to_empty_hash_closes_reader(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.add_init_script("window.__nativePopStates = []; addEventListener('popstate', event => window.__nativePopStates.push({href: location.href, isTrusted: event.isTrusted}));")
        page.goto(urljoin(BASE_URL, "#pakistan-2026-summer-photos/1"), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        page.go_back(wait_until="domcontentloaded", timeout=10000)
        page.wait_for_function("window.__nativePopStates.some(event => event.isTrusted)", timeout=5000)
        result = page.evaluate("({hash: location.hash, reading: document.body.classList.contains('is-reading'), events: window.__nativePopStates})")
        context.close()
        self.assertEqual(result["hash"], "")
        self.assertTrue(any(event["isTrusted"] for event in result["events"]))
        self.assertFalse(result["reading"])


if __name__ == "__main__":
    unittest.main()
