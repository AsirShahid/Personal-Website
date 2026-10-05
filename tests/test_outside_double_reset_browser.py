import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-double-reset"))


class DoubleResetBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def exercise_reset(self, touch):
        context = self.browser.new_context(
            viewport={"width": 390 if touch else 1440, "height": 844 if touch else 900},
            has_touch=True, is_mobile=touch, reduced_motion="reduce")
        try:
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE_URL + "#new-zealand-2026-july-photos/1", wait_until="domcontentloaded")
            page.wait_for_function("""() => {
                const im=document.querySelector('[data-cells] img');
                return im?.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want;
            }""")
            image = page.locator("[data-cells] img").first
            image.evaluate("im=>im.decode()")
            source = image.get_attribute("data-want")
            initial_filter = image.evaluate("im=>im.closest('[data-cells]').style.filter")
            box = image.locator("..").bounding_box()
            assert box is not None
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            page.keyboard.press("w")
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.mouse.move(cx + 45, cy - 20, steps=4)
            page.mouse.up()
            changed_filter = image.evaluate("im=>im.closest('[data-cells]').style.filter")
            self.assertNotEqual(changed_filter, initial_filter)
            page.keyboard.press("i")
            page.keyboard.press("s")
            page.keyboard.press("Equal")
            page.keyboard.press("Equal")
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.mouse.move(cx + 40, cy + 30, steps=4)
            page.mouse.up()
            matrix = lambda: image.evaluate("""im=>{const m=new DOMMatrixReadOnly(getComputedStyle(im).transform);
                return {scale:m.a,x:m.e,y:m.f,source:im.dataset.want,filter:im.style.filter};}""")
            before = matrix()
            self.assertGreater(before["scale"], 1.1)
            self.assertGreater(abs(before["x"]) + abs(before["y"]), 1)
            self.assertEqual(before["source"], source)
            mode = "double-tap" if touch else "double-click"
            page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / f"{mode}-before.png"))
            if touch:
                page.touchscreen.tap(cx, cy)
                page.touchscreen.tap(cx, cy)
            else:
                page.mouse.dblclick(cx, cy)
            after = matrix()
            self.assertAlmostEqual(after["scale"], 1, delta=0.01, msg=mode)
            self.assertAlmostEqual(after["x"], 0, delta=1, msg=mode)
            self.assertAlmostEqual(after["y"], 0, delta=1, msg=mode)
            self.assertEqual(after["source"], source)
            self.assertIn("INVERTED", page.locator('[data-ov="br"]').inner_text())
            # Invert is deliberately retained; switching it off should recover the exact default filter.
            page.keyboard.press("i")
            self.assertEqual(image.evaluate("im=>im.closest('[data-cells]').style.filter"), initial_filter)
            page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / f"{mode}-after.png"))
            self.assertEqual(errors, [])
        finally:
            context.close()

    def test_mobile_double_tap_resets_geometry_and_window_level(self):
        self.exercise_reset(True)

    def test_desktop_double_click_resets_geometry_and_window_level(self):
        self.exercise_reset(False)


if __name__ == "__main__":
    unittest.main()
