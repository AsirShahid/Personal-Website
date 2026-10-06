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
# Colour checks read the settled style, not a frame inside the .15s colour transition.
NO_TRANSITIONS = "*, *::before, *::after { transition: none !important; }"


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

    # ---- Fit must not stay lit after it is pressed (owner report: grey -> white, then stuck) ----

    def lit_state(self, page):
        return page.evaluate("""() => {
          const fit = document.querySelector('button[data-fit]');
          const cs = getComputedStyle(fit);
          return {fit: cs.color, rest: getComputedStyle(document.querySelector('button[data-cine]')).color,
                  outline: cs.outlineStyle, hoverStuck: fit.matches(':hover'),
                  canHover: matchMedia('(hover: hover)').matches,
                  focusOnViewport: document.activeElement === document.querySelector('[data-viewport]'),
                  focusOnFit: document.activeElement === fit};
        }""")

    def series_opacities(self, page):
        return page.evaluate("""() => Array.from(document.querySelectorAll('[data-series] .oz-se')).map(se => ({
          active: se.classList.contains('is-active'), hover: se.matches(':hover'),
          opacity: Number(getComputedStyle(se.querySelector('img')).opacity)}))""")

    def test_tapped_fit_and_series_thumbs_do_not_stay_lit_on_touch_screens(self):
        browser_name = os.environ.get("OUTSIDE_BROWSER", "chromium")
        for label, viewport in (("tablet", {"width": 1180, "height": 820}), ("phone", {"width": 390, "height": 844})):
            with self.subTest(viewport=label):
                context = self.browser.new_context(viewport=viewport, has_touch=True, is_mobile=True, reduced_motion="reduce")
                page = context.new_page()
                self.open_reader(page, viewport["width"] < 900)
                page.add_style_tag(content=NO_TRANSITIONS)
                fit = page.locator("button[data-fit]")
                fit.tap()
                state = self.lit_state(page)
                self.assertFalse(state["canHover"], "this case must exercise a touch-only screen")
                self.assertTrue(state["hoverStuck"], f"{browser_name} keeps :hover on the tapped button; the fix must not rely on it clearing")
                self.assertEqual(state["fit"], state["rest"], "tapped Fit must return to the resting colour")
                page.keyboard.press("ArrowDown")  # browsing after the tap must not light it either
                state = self.lit_state(page)
                self.assertEqual((state["fit"], state["outline"]), (state["rest"], "none"))

                # Series strip: a tapped thumbnail must not stay lit next to the newly active one.
                thumbs = page.locator("[data-series] .oz-se")
                if thumbs.count() >= 2:
                    thumbs.nth(1).tap()
                    page.wait_for_function("() => document.querySelectorAll('[data-series] .oz-se')[1].classList.contains('is-active')")
                    page.keyboard.press("PageUp")
                    page.wait_for_function("() => document.querySelectorAll('[data-series] .oz-se')[0].classList.contains('is-active')")
                    rows = self.series_opacities(page)
                    self.assertTrue(rows[1]["hover"], "the tapped thumbnail keeps a sticky :hover")
                    self.assertEqual([row["opacity"] == 1 for row in rows], [row["active"] for row in rows],
                                     f"only the active series thumbnail may be at full opacity: {rows}")
                context.close()

    def test_mouse_click_on_fit_hands_keys_back_to_the_viewer_and_keyboard_activation_keeps_focus(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        self.open_reader(page, False)
        page.add_style_tag(content=NO_TRANSITIONS)
        fit = page.locator("button[data-fit]")
        fit.hover()
        state = self.lit_state(page)
        self.assertTrue(state["canHover"])
        self.assertNotEqual(state["fit"], state["rest"], "mouse hover feedback must stay on pointer devices")

        fit.click()
        box = page.locator("[data-viewport]").bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        before = page.locator("[data-cells] img").first.get_attribute("data-want")
        page.keyboard.press("ArrowDown")
        page.wait_for_function("prev => document.querySelector('[data-cells] img')?.dataset.want !== prev", arg=before, timeout=5000)
        state = self.lit_state(page)
        self.assertEqual((state["fit"], state["outline"]), (state["rest"], "none"),
                         "an arrow key after clicking Fit must not light Fit up")
        self.assertTrue(state["focusOnViewport"], "a clicked toolbar button hands focus back to the viewer")

        # Space now drives the viewer (Cine) instead of re-pressing Fit.
        page.keyboard.press(" ")
        self.assertEqual(page.locator("button[data-cine]").get_attribute("aria-pressed"), "true")
        page.keyboard.press(" ")
        self.assertEqual(page.locator("button[data-cine]").get_attribute("aria-pressed"), "false")

        # Keyboard users who Tab to Fit and press Enter keep focus there (no focus theft).
        fit.focus()
        page.keyboard.press("Enter")
        self.assertTrue(self.lit_state(page)["focusOnFit"])
        context.close()
