import os
import unittest
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
STUDY = "pakistan-2026-summer-gallery-20261005"
REMOVED_CONTROLS = ".oz-review, [data-review-flag], [data-review-export], [data-review-count], [data-review-saved]"
SCALE = "im => new DOMMatrixReadOnly(getComputedStyle(im).transform).a"
ZOOMED = "() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a > 1.05"
FITTED = "() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a < 1.01"


class OutsideReaderToolbarBrowserTests(unittest.TestCase):
    """Owner-requested changes: no flag/export row, and Fit reads as a plain button."""

    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "chromium")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def open_reader(self, page, mobile):
        page.goto(urljoin(BASE_URL, f"#{STUDY}/1"), wait_until="domcontentloaded")
        if mobile:
            page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        page.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)

    def reader_rows(self, page):
        return page.locator("[data-reader]").evaluate("""el => ({
            rows: Array.from(el.children).map(child => child.className.split(' ')[0]),
            bands: Array.from(el.children).map(child => {
              const box = child.getBoundingClientRect();
              return {top: box.top, bottom: box.bottom, height: box.height};
            }),
        })""")

    def test_review_row_is_gone_and_the_reader_keeps_three_clean_rows(self):
        for label, viewport, mobile in (("desktop", {"width": 1440, "height": 1000}, False),
                                        ("mobile", {"width": 390, "height": 844}, True)):
            with self.subTest(viewport=label):
                context = self.browser.new_context(viewport=viewport, reduced_motion="reduce")
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                self.open_reader(page, mobile)
                self.assertEqual(page.locator(REMOVED_CONTROLS).count(), 0, "the flag/export row must not exist any more")

                geometry = self.reader_rows(page)
                self.assertEqual(geometry["rows"], ["oz-tools", "oz-viewport", "oz-series"],
                                 "the viewer grid must not keep an empty band where the review row was")
                tools, viewport_band, series = geometry["bands"]
                self.assertAlmostEqual(tools["bottom"], viewport_band["top"], delta=0.5, msg="gap above the photo")
                self.assertAlmostEqual(viewport_band["bottom"], series["top"], delta=0.5, msg="gap below the photo")
                self.assertGreater(viewport_band["height"], 0)

                # Browsing must not write the removed review store either.
                page.keyboard.press("ArrowDown")
                stored = page.evaluate("Object.keys(window.localStorage)")
                self.assertFalse([key for key in stored if "photo-review" in key], stored)
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),
                                     page.evaluate("window.innerWidth"))
                self.assertEqual(errors, [], errors)
                context.close()

    def test_fit_is_styled_like_a_plain_button_and_has_no_toggle_state(self):
        for label, viewport, mobile in (("desktop", {"width": 1440, "height": 1000}, False),
                                        ("mobile", {"width": 390, "height": 844}, True)):
            with self.subTest(viewport=label):
                context = self.browser.new_context(viewport=viewport, reduced_motion="reduce")
                page = context.new_page()
                self.open_reader(page, mobile)
                fit = page.locator("button[data-fit]")
                self.assertTrue(fit.is_visible(), "Fit is still a working button on this viewport")
                self.assertIsNone(fit.get_attribute("aria-pressed"), "Fit is a momentary action, not a toggle")

                colors = page.evaluate("""() => {
                  const color = selector => getComputedStyle(document.querySelector(selector)).color;
                  return {fit: color('button[data-fit]'), reset: color('button[data-reset]'),
                          inactiveCine: color('button[data-cine]'), pressedInfo: color('button[data-info]')};
                }""")
                self.assertEqual(colors["fit"], colors["inactiveCine"], "Fit must match an inactive toolbar button")
                if page.locator("button[data-reset]").is_visible():
                    self.assertEqual(colors["fit"], colors["reset"])
                self.assertNotEqual(colors["fit"], colors["pressedInfo"],
                                    "Fit must not wear the pressed/toggled accent")

                # Still the momentary action it always was: zoom in, click Fit, geometry resets.
                image = page.locator("[data-cells] img").first
                page.keyboard.press("+")
                page.wait_for_function(ZOOMED, timeout=5000)
                self.assertGreater(image.evaluate(SCALE), 1.05)
                fit.click()
                page.wait_for_function(FITTED, timeout=5000)
                self.assertAlmostEqual(image.evaluate(SCALE), 1, delta=0.01)
                context.close()
