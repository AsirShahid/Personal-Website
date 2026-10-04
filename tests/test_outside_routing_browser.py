import os
import unittest
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")


LEGACY_SOURCE_EXPECTATIONS = {'projection-american-southwest-2025': ['/outside/assets/core-trips/0072', '/outside/assets/core-trips/0214', '/outside/assets/core-trips/0245', '/outside/assets/core-trips/0307', '/outside/zion/010', '/outside/zion/020', '/outside/zion/026', '/outside/assets/core-trips/0398', '/outside/zion/032', '/outside/assets/core-trips/0431', '/outside/assets/core-trips/0436', '/outside/assets/core-trips/0458', '/outside/assets/core-trips/0479', '/outside/assets/core-trips/0487', '/outside/assets/core-trips/0562', '/outside/assets/core-trips/0586', '/outside/assets/core-trips/0608', '/outside/hoover-dam/005', '/outside/assets/core-trips/0614', '/outside/hoover-dam/013', '/outside/hoover-dam/017', '/outside/hoover-dam/020']}

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
        page.wait_for_timeout(500)
        return context, page

    def image_src(self, page):
        src = page.locator("[data-cells] img").first.get_attribute("src")
        for suffix in ("-s.webp", "-m.webp", "-l.webp"):
            if src.endswith(suffix):
                return src[: -len(suffix)]
        return src

    def expected_src(self, page, study_id, image_index):
        data = page.locator("#oz-data").text_content()
        import json
        payload = json.loads(data)
        if study_id in LEGACY_SOURCE_EXPECTATIONS:
            return LEGACY_SOURCE_EXPECTATIONS[study_id][image_index]
        study = next(item for item in payload["studies"] if item["id"] == study_id)
        return study["images"][image_index]["src"]

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
                page.wait_for_timeout(650)
                self.assertTrue(alert.is_visible())
                self.assertEqual(page.evaluate("location.hash"), "#not-a-supported-study/1")
                context.close()

    def test_popstate_unavailable_keeps_error_and_fragment_after_deferred_timers(self):
        for width in (1440, 390):
            with self.subTest(width=width):
                context, page = self.open_page("#projection-pakistan-2026/1", width)
                page.evaluate("history.pushState({test: true}, '', '#not-a-supported-study/2'); window.dispatchEvent(new PopStateEvent('popstate'))")
                page.wait_for_timeout(650)
                self.assertTrue(page.locator("[data-route-error]").is_visible())
                self.assertEqual(page.evaluate("location.hash"), "#not-a-supported-study/2")
                self.assertEqual(page.locator("[data-reader]").evaluate("el => getComputedStyle(el).visibility"), "hidden")
                context.close()

    def test_partial_alias_keeps_exact_old_source_mappings_and_explicit_holes(self):
        for width in (1440, 390):
            with self.subTest(width=width):
                for fragment, image_index in (("#hoover-dam", 17), ("#hoover-dam/1", 17), ("#zion/1", 4), ("#american-southwest-2025", 4), ("#american-southwest-2025/2", 4)):
                    context, page = self.open_page(fragment, width)
                    self.assertEqual(self.image_src(page), self.expected_src(page, "projection-american-southwest-2025", image_index), fragment)
                    context.close()
                context, page = self.open_page("#hoover-dam/10", width)
                self.assertTrue(page.locator("[data-route-error]").is_visible())
                self.assertEqual(page.evaluate("location.hash"), "#hoover-dam/10")
                context.close()

    def test_invalid_alias_ordinals_are_rejected_but_direct_study_clamp_remains(self):
        for width in (1440, 390):
            for route in ("#lahore/999", "#lahore/0", "#lahore/01", "#projection-pakistan-2026/999"):
                with self.subTest(width=width, route=route):
                    context, page = self.open_page(route, width)
                    self.assertTrue(page.locator("[data-route-error]").is_visible())
                    self.assertEqual(page.evaluate("location.hash"), route)
                    context.close()
            context, page = self.open_page("#projection-pakistan-2026-expanded/999", width)
            self.assertEqual(self.image_src(page), self.expected_src(page, "projection-pakistan-2026-expanded", -1))
            context.close()

    def test_valid_selection_recovers_and_summer_heading_is_absent_on_desktop_and_mobile(self):
        for width in (1440, 390):
            with self.subTest(width=width):
                context, page = self.open_page("#not-a-supported-study", width)
                page.locator('[data-study="0"]').click()
                page.wait_for_timeout(500)
                self.assertFalse(page.locator("[data-route-error]").is_visible())
                self.assertEqual(page.locator('[data-study="0"]').get_attribute("aria-current"), "true")
                self.assertEqual(page.locator(".oz-journey").count(), 0)
                context.close()

    def test_mobile_native_back_from_reader_to_empty_hash_closes_reader(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.add_init_script("window.__nativePopStates = []; addEventListener('popstate', event => window.__nativePopStates.push({href: location.href, isTrusted: event.isTrusted}));")
        page.goto(urljoin(BASE_URL, "#projection-pakistan-2026/1"), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        page.go_back(wait_until="domcontentloaded", timeout=10000)
        page.wait_for_function("window.__nativePopStates.some(event => event.isTrusted)", timeout=5000)
        result = page.evaluate("({hash: location.hash, reading: document.body.classList.contains('is-reading'), events: window.__nativePopStates})")
        print("NATIVE_HISTORY_RESULT", result)
        context.close()
        self.assertEqual(result["hash"], "")
        self.assertTrue(any(event["isTrusted"] for event in result["events"]))
        self.assertFalse(result["reading"])


if __name__ == "__main__":
    unittest.main()
