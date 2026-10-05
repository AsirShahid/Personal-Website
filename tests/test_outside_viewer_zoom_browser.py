import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR") or tempfile.mkdtemp(prefix="outside-viewer-zoom-"))
STUDY_ID = "new-zealand-2026-july-photos"


class OutsideViewerZoomBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "chromium")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    @staticmethod
    def photo_matrix(page):
        return page.locator("[data-cells] .oz-cell img").first.evaluate("""im => {
          const m = new DOMMatrixReadOnly(getComputedStyle(im).transform);
          return {a:m.a, d:m.d, e:m.e, f:m.f, src:im.dataset.want, currentSrc:new URL(im.currentSrc).pathname,
            complete:im.complete, naturalWidth:im.naturalWidth, naturalHeight:im.naturalHeight};
        }""")

    def test_grid_pinch_only_transforms_the_target_cell_and_fit_resets_visible_cells(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, has_touch=True, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, f"#{STUDY_ID}/1"), wait_until="domcontentloaded")
        page.wait_for_function("""() => { const im=document.querySelector('[data-cells] img'); return im?.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want; }""", timeout=15000)
        page.locator("button[data-layout]").click()
        page.wait_for_function("""() => [...document.querySelectorAll('[data-cells] .oz-cell img')].length===4 && [...document.querySelectorAll('[data-cells] .oz-cell img')].every(im=>im.complete&&im.naturalWidth>0)""", timeout=15000)
        self.assertEqual(page.locator("[data-cells] .oz-cell").count(), 4)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "grid-before.png"))
        overlays_before = page.locator(".oz-ov").evaluate_all("els => els.map(el => { const r=el.getBoundingClientRect(); return [r.x,r.y,r.width,r.height]; })")
        image_sources = page.locator("[data-cells] .oz-cell img").evaluate_all("els => els.map(im=>im.dataset.want)")
        target = page.locator("[data-cells] .oz-cell img").nth(1)
        center = target.evaluate("""im => { const c=im.closest('.oz-cell'),r=c.getBoundingClientRect(); return {x:r.left+r.width/2,y:r.top+r.height/2}; }""")
        cdp = context.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[
            {"id":10,"x":center["x"]-22,"y":center["y"],"radiusX":5,"radiusY":5,"force":1},
            {"id":11,"x":center["x"]+22,"y":center["y"],"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[
            {"id":10,"x":center["x"]-68,"y":center["y"],"radiusX":5,"radiusY":5,"force":1},
            {"id":11,"x":center["x"]+68,"y":center["y"],"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        page.wait_for_function("() => new DOMMatrixReadOnly(getComputedStyle(document.querySelectorAll('[data-cells] .oz-cell img')[1]).transform).a>1.5")
        matrices = page.locator("[data-cells] .oz-cell img").evaluate_all("els => els.map(im=>{const m=new DOMMatrixReadOnly(getComputedStyle(im).transform);return {a:m.a,d:m.d,e:m.e,f:m.f};})")
        self.assertGreater(matrices[1]["a"], 1.5)
        self.assertEqual([round(m["a"], 2) for i,m in enumerate(matrices) if i != 1], [1,1,1])
        self.assertEqual(page.locator("[data-cells]").get_attribute("data-layout"), "4")
        self.assertEqual(page.locator("[data-cells] .oz-cell img").evaluate_all("els=>els.map(im=>im.dataset.want)"), image_sources)
        overlays_after = page.locator(".oz-ov").evaluate_all("els => els.map(el => { const r=el.getBoundingClientRect(); return [r.x,r.y,r.width,r.height]; })")
        for before, after in zip(overlays_before, overlays_after):
            for a, b in zip(before, after): self.assertAlmostEqual(a, b, delta=0.5)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "grid-one-cell-zoom.png"))
        page.locator("[data-fit]").click()
        fitted = page.locator("[data-cells] .oz-cell img").evaluate_all("els => els.map(im=>{const m=new DOMMatrixReadOnly(getComputedStyle(im).transform);return {a:m.a,d:m.d,e:m.e,f:m.f};})")
        self.assertTrue(all(abs(m["a"]-1)<0.01 and abs(m["d"]-1)<0.01 and abs(m["e"])<1 and abs(m["f"])<1 for m in fitted), fitted)
        self.assertEqual(page.locator("[data-cells]").get_attribute("data-layout"), "4")
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "grid-after-fit.png"))
        page.locator("button[data-layout]").click()
        self.assertEqual(page.locator("[data-cells]").get_attribute("data-layout"), "1")
        self.assertAlmostEqual(self.photo_matrix(page)["a"], 1, delta=0.01)
        self.assertEqual(errors, [], errors)
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 1440)
        context.close()

    def test_mobile_pinch_pan_fit_cancel_and_letterbox_stay_in_viewport(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, f"#{STUDY_ID}/1"), wait_until="domcontentloaded")
        page.wait_for_function("""() => document.body.classList.contains('is-reading') && (() => {const im=document.querySelector('[data-cells] img');return im&&im.complete&&im.naturalWidth>0&&new URL(im.currentSrc).pathname===im.dataset.want;})()""", timeout=15000)
        image = page.locator("[data-cells] .oz-cell img").first
        image.evaluate("im=>im.decode()")
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-mobile-before.png"))
        source = self.photo_matrix(page)["src"]
        rect = image.evaluate("""im => {const c=im.closest('.oz-cell'),r=c.getBoundingClientRect(),f=Math.min(r.width/Number(im.getAttribute('width')),r.height/Number(im.getAttribute('height'))),w=Number(im.getAttribute('width'))*f,h=Number(im.getAttribute('height'))*f;return {x:r.left+r.width/2,y:r.top+r.height/2,left:r.left+(r.width-w)/2,top:r.top+(r.height-h)/2,width:w,height:h,cellTop:r.top,cellHeight:r.height};}""")
        cdp = context.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[
            {"id":20,"x":rect["x"]-20,"y":rect["y"],"radiusX":5,"radiusY":5,"force":1},
            {"id":21,"x":rect["x"]+20,"y":rect["y"],"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[
            {"id":20,"x":rect["x"]-58,"y":rect["y"],"radiusX":5,"radiusY":5,"force":1},
            {"id":21,"x":rect["x"]+58,"y":rect["y"],"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        page.wait_for_function("() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a>1.5")
        zoomed = self.photo_matrix(page)
        self.assertEqual(zoomed["src"], source)
        self.assertGreater(zoomed["a"], 1.5)
        self.assertEqual(page.locator("[data-cells]").get_attribute("data-layout"), "1")
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-mobile-after-pinch.png"))

        # One-finger touch pans while zoomed, without scrolling the document.
        before_scroll = page.evaluate("scrollY")
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[{"id":22,"x":rect["x"],"y":rect["y"],"radiusX":5,"radiusY":5,"force":1}]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[{"id":22,"x":rect["x"]+18,"y":rect["y"]+8,"radiusX":5,"radiusY":5,"force":1}]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        panned = self.photo_matrix(page)
        self.assertEqual(panned["src"], source)
        self.assertGreater(abs(panned["e"])+abs(panned["f"]), 10)
        self.assertEqual(page.evaluate("scrollY"), before_scroll)

        # Fit returns to true 1x before dragging from the image's actual letterbox.
        page.locator("[data-fit]").click()
        fitted = self.photo_matrix(page)
        self.assertAlmostEqual(fitted["a"], 1, delta=0.01)
        letterbox_y = min(rect["cellTop"]+rect["cellHeight"]-4, rect["top"]+rect["height"]+12)
        self.assertGreater(letterbox_y, rect["top"]+rect["height"])
        self.assertLess(letterbox_y, rect["cellTop"]+rect["cellHeight"])
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[{"id":23,"x":rect["x"],"y":letterbox_y,"radiusX":5,"radiusY":5,"force":1}]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[{"id":23,"x":rect["x"]+6,"y":letterbox_y+24,"radiusX":5,"radiusY":5,"force":1}]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        page.wait_for_function("src => document.querySelector('[data-cells] img').dataset.want !== src", arg=source)
        letterbox_source = self.photo_matrix(page)["src"]
        self.assertEqual(page.evaluate("scrollY"), before_scroll)
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)

        # Native cancellation clears the captured gesture instead of leaving drag state behind.
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[{"id":24,"x":rect["x"],"y":rect["y"],"radiusX":5,"radiusY":5,"force":1}]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchCancel","touchPoints":[]})
        page.wait_for_function("!document.querySelector('[data-viewport]').classList.contains('is-dragging')")
        page.locator("[data-fit]").click()
        fit = self.photo_matrix(page)
        self.assertAlmostEqual(fit["a"], 1, delta=0.01)
        self.assertAlmostEqual(fit["e"], 0, delta=1)
        self.assertEqual(fit["src"], letterbox_source)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-mobile-after-fit.png"))
        self.assertEqual(errors, [], errors)
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)
        context.close()

    def test_native_pinch_pan_fit_and_wheel_gestures(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 900}, has_touch=True, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, f"#{STUDY_ID}/1"), wait_until="domcontentloaded")
        page.wait_for_function("""() => {
          const im=document.querySelector('[data-cells] img');
          return im && im.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want;
        }""", timeout=15000)
        image = page.locator("[data-cells] .oz-cell img").first
        image.evaluate("im => im.decode()")
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-before.png"))
        initial = self.photo_matrix(page)
        self.assertGreater(initial["naturalWidth"], 0)
        source_before = initial["src"]

        # Set non-default display modifiers to ensure photo zoom cannot reset them.
        page.locator('[data-tool="wl"]').click()
        box = page.locator("[data-viewport]").bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + 45, cy - 18, steps=5)
        page.mouse.up()
        wl_before = page.locator('[data-ov="br"]').inner_text()
        page.locator("[data-invert]").click()
        wl_before = page.locator('[data-ov="br"]').inner_text()
        self.assertIn("INVERTED", wl_before)

        # Two native Chromium touch points via CDP must zoom without changing W/L or scrubbing.
        cdp = page.context.new_cdp_session(page)
        center = image.evaluate("""im => {
          const r=im.closest('.oz-cell').getBoundingClientRect();
          const fit=Math.min(r.width/im.width,r.height/im.height), w=im.width*fit, h=im.height*fit;
          return {x:r.left+(r.width-w)/2+w/2,y:r.top+(r.height-h)/2+h/2};
        }""")
        cx, cy = center["x"], center["y"]
        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[
            {"id":1,"x":cx-24,"y":cy,"radiusX":5,"radiusY":5,"force":1},
            {"id":2,"x":cx+24,"y":cy,"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[
            {"id":1,"x":cx-55,"y":cy+12,"radiusX":5,"radiusY":5,"force":1},
            {"id":2,"x":cx+85,"y":cy+12,"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        page.wait_for_function("""() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a > 1.5""", timeout=2500)
        after_pinch = self.photo_matrix(page)
        diagnostic = {"after": after_pinch, "center": center, "style": image.evaluate("im=>({inline:im.style.transform,computed:getComputedStyle(im).transform,origin:getComputedStyle(im).transformOrigin})"), "cell": image.evaluate("im=>{const r=im.closest('.oz-cell').getBoundingClientRect(),f=Math.min(r.width/Number(im.getAttribute('width')),r.height/Number(im.getAttribute('height')));return {x:r.x,y:r.y,width:r.width,height:r.height,fitWidth:Number(im.getAttribute('width'))*f,fitHeight:Number(im.getAttribute('height'))*f,widthAttr:im.getAttribute('width'),heightAttr:im.getAttribute('height')}}")}
        self.assertEqual(after_pinch["src"], source_before, "pinch must not scrub the stack")
        self.assertGreater(after_pinch["a"], 1.5)
        self.assertAlmostEqual(after_pinch["e"], 15, delta=1, msg=repr(diagnostic))
        self.assertAlmostEqual(after_pinch["f"], 12, delta=1, msg=repr(diagnostic))
        self.assertEqual(page.locator("[data-viewport]").get_attribute("data-tool"), "wl")
        self.assertEqual(page.locator('[data-ov="br"]').inner_text(), wl_before)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-after-pinch.png"))

        # W/L remains an explicit single-pointer mode even while the photo is zoomed.
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + 30, cy + 20, steps=4)
        page.mouse.up()
        wl_after_drag = page.locator('[data-ov="br"]').inner_text()
        wl_matrix = self.photo_matrix(page)
        self.assertNotEqual(wl_after_drag, wl_before)
        self.assertAlmostEqual(wl_matrix["a"], after_pinch["a"], delta=0.02)
        self.assertAlmostEqual(wl_matrix["e"], after_pinch["e"], delta=1)
        self.assertAlmostEqual(wl_matrix["f"], after_pinch["f"], delta=1)

        # In Stack mode a trusted mouse drag pans the zoomed photo rather than scrubbing.
        page.locator('[data-tool="stack"]').click()
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + 42, cy + 24, steps=5)
        page.mouse.up()
        panned = self.photo_matrix(page)
        self.assertEqual(panned["src"], source_before)
        self.assertAlmostEqual(panned["a"], after_pinch["a"], delta=0.02)
        self.assertGreater(abs(panned["e"]-after_pinch["e"])+abs(panned["f"]-after_pinch["f"]), 10)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-after-pan.png"))

        # Pan clamps to the contained photo's bounds, not the full CSS image box.
        cell = image.evaluate("im => { const c=im.closest('.oz-cell'), r=c.getBoundingClientRect(); const f=Math.min(r.width/Number(im.getAttribute('width')),r.height/Number(im.getAttribute('height'))); return {width:r.width,height:r.height,fitWidth:Number(im.getAttribute('width'))*f,fitHeight:Number(im.getAttribute('height'))*f,centerX:r.left+r.width/2,centerY:r.top+r.height/2}; }")
        scale_for_clamp = self.photo_matrix(page)["a"]
        page.mouse.move(cell["centerX"], cell["centerY"])
        page.mouse.down()
        page.mouse.move(cell["centerX"] + 500, cell["centerY"], steps=8)
        page.mouse.up()
        clamped = self.photo_matrix(page)
        max_x = max(0, (cell["fitWidth"] * scale_for_clamp - cell["width"]) / 2)
        self.assertAlmostEqual(clamped["e"], max_x, delta=2)

        # Ctrl-wheel zooms at its pointer; Fit changes geometry only; ordinary wheel still pages while zoomed.
        scale_before_wheel = self.photo_matrix(page)["a"]
        wheel_anchor = {"x": cell["centerX"] + 100, "y": cell["centerY"] - 50}
        before_matrix = self.photo_matrix(page)
        before_point_x = (wheel_anchor["x"] - cell["centerX"] - before_matrix["e"]) / before_matrix["a"]
        page.keyboard.down("Control")
        page.mouse.move(wheel_anchor["x"], wheel_anchor["y"])
        page.mouse.wheel(0, -120)
        page.keyboard.up("Control")
        page.wait_for_function("""() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a > 1.1""")
        after_wheel = self.photo_matrix(page)
        self.assertGreater(after_wheel["a"], scale_before_wheel)
        self.assertEqual(after_wheel["src"], source_before)
        after_point_x = (wheel_anchor["x"] - cell["centerX"] - after_wheel["e"]) / after_wheel["a"]
        self.assertAlmostEqual(after_point_x, before_point_x, delta=0.02)
        self.assertTrue(page.locator("[data-fit]").is_visible())
        wl_before_fit = page.locator('[data-ov="br"]').inner_text()
        page.locator("[data-fit]").click()
        fit = self.photo_matrix(page)
        self.assertAlmostEqual(fit["a"], 1, delta=0.01)
        self.assertAlmostEqual(fit["d"], 1, delta=0.01)
        self.assertAlmostEqual(fit["e"], 0, delta=1)
        self.assertAlmostEqual(fit["f"], 0, delta=1)
        self.assertEqual(page.locator('[data-ov="br"]').inner_text(), wl_before_fit)
        page.locator("[data-viewport]").screenshot(path=str(EVIDENCE / "zoom-after-fit.png"))

        # Keyboard zoom is an accessible alternate path; R resets all view modifiers.
        page.keyboard.press("Shift+=")
        self.assertGreater(self.photo_matrix(page)["a"], 1)
        page.keyboard.press("-")
        self.assertAlmostEqual(self.photo_matrix(page)["a"], 1, delta=0.01)
        for _ in range(24): page.keyboard.press("Shift+=")
        self.assertAlmostEqual(self.photo_matrix(page)["a"], 8, delta=0.01)
        self.assertLessEqual(self.photo_matrix(page)["a"], 8)
        for _ in range(24): page.keyboard.press("-")
        self.assertAlmostEqual(self.photo_matrix(page)["a"], 1, delta=0.01)
        page.keyboard.press("Shift+=")
        page.keyboard.press("r")
        reset = self.photo_matrix(page)
        self.assertAlmostEqual(reset["a"], 1, delta=0.01)
        reset_overlay = page.locator('[data-ov="br"]').inner_text()
        self.assertIn("W 255  L 128", reset_overlay)
        self.assertNotIn("INVERTED", reset_overlay)

        # An unzoomed drag retains the familiar fit-to-stack scrub.
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx, cy + 18, steps=1)
        page.mouse.up()
        page.wait_for_function("src => document.querySelector('[data-cells] img').dataset.want !== src", arg=source_before)
        self.assertAlmostEqual(self.photo_matrix(page)["a"], 1, delta=0.01)
        page.keyboard.press("ArrowLeft")
        page.wait_for_function("src => document.querySelector('[data-cells] img').dataset.want === src", arg=source_before)

        cdp.send("Input.dispatchTouchEvent", {"type":"touchStart","touchPoints":[
            {"id":3,"x":cx-24,"y":cy,"radiusX":5,"radiusY":5,"force":1},
            {"id":4,"x":cx+24,"y":cy,"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchMove","touchPoints":[
            {"id":3,"x":cx-55,"y":cy+12,"radiusX":5,"radiusY":5,"force":1},
            {"id":4,"x":cx+85,"y":cy+12,"radiusX":5,"radiusY":5,"force":1},
        ]})
        cdp.send("Input.dispatchTouchEvent", {"type":"touchEnd","touchPoints":[]})
        page.wait_for_function("() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a > 1.5")
        page.mouse.move(cx, cy)
        page.mouse.wheel(0, 160)
        page.wait_for_function("src => document.querySelector('[data-cells] img').dataset.want !== src", arg=source_before)
        page.wait_for_function("() => Math.abs(new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] img')).transform).a - 1) < .01")
        self.assertEqual(errors, [], errors)
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 1440)
        context.close()


if __name__ == "__main__":
    unittest.main()
