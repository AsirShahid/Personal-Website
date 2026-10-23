"""How-to hint and tap navigation in the Outside reader.

- The hint shows soon after the first study opens, and again when someone opens a study and stays on its opening photo.
  Moving to another photo hides it for that study.
- On touch screens the hint marks the two tap zones, and a tap on either side steps at once instead of waiting to see
  whether a double-tap follows. While zoomed, a double-tap still resets the view.
"""
import json
import os
import unittest
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
ENGINE = os.environ.get("OUTSIDE_BROWSER", "chromium")
HINT_SHOWN = "() => !document.querySelector('[data-hint]').classList.contains('is-gone')"
HINT_GONE = "() => document.querySelector('[data-hint]').classList.contains('is-gone')"
PHOTO_READY = """() => { const im = document.querySelector('[data-cells] img');
  return im && im.complete && im.naturalWidth > 0 && new URL(im.currentSrc).pathname === im.dataset.want; }"""
TAP_CLOCK = """
window.__tapUp = 0;
addEventListener('pointerup', (e) => { if (e.pointerType !== 'mouse') window.__tapUp = performance.now(); }, true);
"""
STEP_DELAY = """(prev) => new Promise((resolve) => {
  const start = performance.now();
  const tick = () => {
    const want = document.querySelector('[data-cells] img').dataset.want;
    if (want !== prev) resolve(performance.now() - window.__tapUp);
    else if (performance.now() - start > 3000) resolve(null);
    else requestAnimationFrame(tick);
  };
  tick();
})"""


def payload(page):
    return json.loads(page.locator("#oz-data").text_content() or "{}")


def stack_position(page):
    return int(page.locator("[data-stackthumb]").get_attribute("data-label"))


class OutsideHintAndTapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = getattr(cls.playwright, ENGINE).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_desktop_hint_returns_when_a_new_study_stays_on_its_opening_photo(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-ready')")
        # First open: shown almost at once, in plain words.
        page.wait_for_function(HINT_SHOWN, timeout=3000)
        self.assertIn("next photo", page.locator(".oz-hint-desk").inner_text())
        self.assertFalse(page.locator(".oz-hint-touch").is_visible())
        # Moving to another photo hides it, and it stays away for this study.
        page.locator("[data-viewport]").focus()
        page.keyboard.press("ArrowDown")
        page.wait_for_function(HINT_GONE, timeout=1000)
        page.wait_for_timeout(6000)
        self.assertTrue(page.evaluate(HINT_GONE), "the hint must not return after moving within the study")

        rows = page.locator(".oz-rows [data-study]")
        self.assertGreaterEqual(rows.count(), 3)
        # Opening another study and staying on its opening photo brings it back, after a pause rather than at once.
        rows.nth(1).click()
        opened = page.evaluate("performance.now()")
        page.wait_for_timeout(2000)
        self.assertTrue(page.evaluate(HINT_GONE), "a repeat visit waits before showing the hint")
        page.wait_for_function(HINT_SHOWN, timeout=8000)
        self.assertGreaterEqual(page.evaluate("performance.now()") - opened, 4000)
        # Opening a study and moving on right away never shows it.
        rows.nth(2).click()
        page.wait_for_timeout(500)
        page.locator("[data-viewport]").focus()
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(6500)
        self.assertTrue(page.evaluate(HINT_GONE), "moving on before the pause means no hint for that study")
        self.assertEqual(errors, [], errors)
        context.close()

    def test_touch_hint_marks_tap_zones_and_side_taps_step_at_once(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True,
                                           has_touch=True, reduced_motion="reduce")
        context.add_init_script(TAP_CLOCK)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE_URL, wait_until="domcontentloaded")
        study = max(payload(page)["studies"], key=lambda s: len(s["images"]))
        page.goto(urljoin(BASE_URL, f"#{study['id']}/{study['images'][0]['id']}"), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        page.wait_for_function(PHOTO_READY, timeout=15000)

        page.wait_for_function(HINT_SHOWN, timeout=3000)
        self.assertIn("Tap right", page.locator(".oz-hint-touch").inner_text())
        self.assertFalse(page.locator(".oz-hint-desk").is_visible())
        zones = page.locator(".oz-tapzone").evaluate_all("els => els.map(el => getComputedStyle(el).opacity)")
        self.assertEqual(zones, ["1", "1"], "both tap zones are marked while the hint shows")

        box = page.locator("[data-viewport]").bounding_box()
        right = (box["x"] + box["width"] * 0.85, box["y"] + box["height"] * 0.5)
        left = (box["x"] + box["width"] * 0.15, box["y"] + box["height"] * 0.5)
        start = stack_position(page)
        delays = []
        for _ in range(3):
            prev = page.locator("[data-cells] img").first.get_attribute("data-want")
            page.touchscreen.tap(*right)
            delays.append(page.evaluate(STEP_DELAY, prev))
            page.wait_for_timeout(450)
        self.assertTrue(page.evaluate(HINT_GONE), "tapping hides the hint")
        self.assertEqual(stack_position(page), start + 3)
        self.assertTrue(all(d is not None and d < 150 for d in delays), f"side taps must not wait for a double-tap: {delays}")
        zones = page.locator(".oz-tapzone").evaluate_all("els => els.map(el => getComputedStyle(el).opacity)")
        self.assertEqual(zones, ["0", "0"])

        page.touchscreen.tap(*left)
        page.wait_for_function("n => Number(document.querySelector('[data-stackthumb]').dataset.label) === n", arg=start + 2)
        # Two quick taps on a side are two steps.
        page.wait_for_timeout(450)
        page.touchscreen.tap(*right)
        page.wait_for_timeout(90)
        page.touchscreen.tap(*right)
        page.wait_for_function("n => Number(document.querySelector('[data-stackthumb]').dataset.label) === n", arg=start + 4, timeout=2000)

        # Zoomed in, a double-tap still resets the view instead of stepping.
        page.wait_for_timeout(450)
        page.keyboard.press("Equal")
        page.keyboard.press("Equal")
        scale = "() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a"
        self.assertGreater(page.evaluate(scale), 1.1)
        position = stack_position(page)
        page.touchscreen.tap(*right)
        page.wait_for_timeout(60)
        page.touchscreen.tap(*right)
        page.wait_for_function(f"() => ({scale})() < 1.01", timeout=2000)
        page.wait_for_timeout(500)
        self.assertEqual(stack_position(page), position, "a double-tap while zoomed resets the view, it does not step")
        self.assertEqual(errors, [], errors)
        context.close()


if __name__ == "__main__":
    unittest.main()
