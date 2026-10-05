"""Camera labels remain visible with Info enabled at phone/tablet/desktop widths."""
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
BASE = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-camera-test"))


@pytest.mark.parametrize("width,height", [(390, 844), (800, 1000), (1280, 900)])
def test_phone_name_is_visible_when_info_is_on(width, height):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    source = "/outside/assets/summer-2026/1035"
    study = next(s for s in DATA["studies"] if any(im["src"] == source for im in s["images"]))
    ordinal = next(i + 1 for i, im in enumerate(study["images"]) if im["src"] == source)
    with sync_playwright() as pw:
        browser = getattr(pw, os.environ.get("OUTSIDE_BROWSER", "chromium")).launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE + f"#{study['id']}/{ordinal}", wait_until="domcontentloaded")
            if width <= 899:
                page.wait_for_function("document.body.classList.contains('is-reading')")
            page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want && im.dataset.want.startsWith(stem); }", arg=source)
            page.locator("[data-cells] img").first.evaluate("im=>im.decode()")
            info = page.locator('[data-info]')
            assert info.get_attribute("aria-pressed") == "true"
            camera = page.locator('[data-ov="bl"] div').filter(has_text="ONEPLUS 11 5G")
            observed = camera.evaluate("el => ({display:getComputedStyle(el).display, width:el.getBoundingClientRect().width, height:el.getBoundingClientRect().height})")
            page.screenshot(path=str(EVIDENCE / f"camera-{width}-info-on.png"))
            assert camera.count() == 1
            assert observed["display"] != "none", f"Camera metadata exists but is hidden at {width}px: {observed}"
            assert observed["width"] > 0 and observed["height"] > 0
            assert "ONEPLUS 11 5G" in page.locator('[data-ov="bl"]').inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            info.click()
            assert info.get_attribute("aria-pressed") == "false"
            assert page.locator('[data-ov="bl"]').evaluate("el=>getComputedStyle(el).opacity") == "0"
            info.click()
            assert info.get_attribute("aria-pressed") == "true"
            assert page.locator('[data-ov="bl"]').evaluate("el=>getComputedStyle(el).opacity") == "1"
            assert camera.is_visible()
            # No guessed phone name is added to an import whose metadata is absent.
            empty = next((s, i + 1, im) for s in DATA["studies"] for i, im in enumerate(s["images"]) if im["src"].endswith("/G004"))
            # Independent metadata case: enter through normal fresh-page boot.
            # Mobile popstate intentionally skips opening another study while
            # its reader is already open, so same-document goto is not this case.
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(BASE + f"#{empty[0]['id']}/{empty[1]}", wait_until="domcontentloaded")
            page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want && im.dataset.want.startsWith(stem); }", arg=empty[2]["src"])
            assert empty[2]["cam"] == ""
            assert page.locator('[data-ov="bl"]').inner_text() == ""
            assert errors == []
        finally:
            browser.close()
