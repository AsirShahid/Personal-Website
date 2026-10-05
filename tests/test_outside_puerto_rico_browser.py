import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
SOURCE = json.loads((ROOT / "src/data/outside-studies.json").read_text())
BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-pr-browser-evidence"))
PR_ID = "puerto-rico-2025-june-gallery"
OLD_ID = "puerto-rico-2025-june"
PR = next(study for study in SOURCE["studies"] if study["id"] == PR_ID)
PR_SOURCES = [image["src"] for image in PR["images"]]


class PuertoRicoCompiledBrowserAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def wait_for_painted_source(self, page, source):
        page.wait_for_function(
            """expected => {
              const im = document.querySelector('[data-cells] img');
              return im && im.complete && im.naturalWidth > 0 && im.naturalHeight > 0 &&
                im.dataset.want && im.dataset.want.startsWith(expected) &&
                new URL(im.currentSrc).pathname === im.dataset.want;
            }""",
            arg=source,
            timeout=15000,
        )
        decoded = page.locator("[data-cells] img").evaluate("async im => { await im.decode(); return {want: im.dataset.want, current: new URL(im.currentSrc).pathname, width: im.naturalWidth, height: im.naturalHeight}; }")
        self.assertEqual(decoded["current"], decoded["want"])
        self.assertGreater(decoded["width"], 0)
        self.assertGreater(decoded["height"], 0)
        return decoded

    def test_compiled_recent_inventory_and_all_46_photo_sources_paint_and_decode(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, f"#{PR_ID}/1"), wait_until="domcontentloaded")
        payload = json.loads(page.locator("#oz-data").text_content() or "{}")
        self.assertEqual((len(payload["studies"]), sum(len(study["images"]) for study in payload["studies"])), (21, 485))
        visible = page.locator(".oz-rows [data-study]")
        visible_ids = [(row.get_attribute("href") or "").lstrip("#") for row in visible.all()]
        self.assertIn(PR_ID, visible_ids)
        self.assertEqual((len(visible_ids), sum(len(study["images"]) for study in SOURCE["studies"] if study["id"] in visible_ids)), (9, 334))
        self.assertIn("9 studies", page.locator(".oz-topmeta").inner_text().lower())
        self.assertIn("334 images", page.locator(".oz-topmeta").inner_text().lower())

        painted = []
        for ordinal, image in enumerate(PR["images"], 1):
            page.goto(urljoin(BASE_URL, f"#{PR_ID}/{ordinal}"), wait_until="domcontentloaded")
            result = self.wait_for_painted_source(page, image["src"])
            self.assertTrue(re.search(r"-(s|m|l)\.webp$", result["current"]))
            painted.append(image["src"])
        self.assertEqual(painted, PR_SOURCES)
        self.assertEqual(len(painted), 46)

        # The old default and ordinal routes keep their original, immutable source targets.
        for route, expected in ((f"#{OLD_ID}", "C887"), (f"#{OLD_ID}/1", "C887"), (f"#{OLD_ID}/2", "C894")):
            page.goto(urljoin(BASE_URL, route), wait_until="domcontentloaded")
            result = self.wait_for_painted_source(page, f"/outside/assets/owner-review/core-trips/{expected}")
            self.assertTrue(result["want"].startswith(f"/outside/assets/owner-review/core-trips/{expected}-"))
        page.goto(urljoin(BASE_URL, "#puerto-rico-2025-october/1"), wait_until="domcontentloaded")
        historical = next(study for study in SOURCE["studies"] if study["id"] == "puerto-rico-2025-october")
        self.assertTrue(self.wait_for_painted_source(page, historical["images"][0]["src"])["want"].startswith(historical["images"][0]["src"]))
        self.assertEqual(errors, [], errors)
        context.close()

    def test_native_review_flags_and_export_cover_all_46_exact_source_keys(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page = context.new_page()
        page.goto(urljoin(BASE_URL, f"#{PR_ID}/1"), wait_until="domcontentloaded")
        self.assertIsNone(page.evaluate("localStorage.getItem('outside-studies:photo-review:v1')"), "acceptance must use a fresh isolated browser context")
        for ordinal, image in enumerate(PR["images"], 1):
            page.goto(urljoin(BASE_URL, f"#{PR_ID}/{ordinal}"), wait_until="domcontentloaded")
            self.wait_for_painted_source(page, image["src"])
            flag = page.locator("[data-review-flag]")
            self.assertEqual(flag.get_attribute("aria-pressed"), "false", image["src"])
            flag.click()
            self.assertEqual(flag.get_attribute("aria-pressed"), "true", image["src"])
        stored = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
        self.assertEqual(set(stored["flaggedSrcs"]), set(PR_SOURCES))
        self.assertEqual(len(stored["flaggedSrcs"]), 46)
        with page.expect_download(timeout=5000) as download_info:
            page.locator("[data-review-export]").click()
        exported = json.loads(Path(download_info.value.path()).read_text())
        self.assertEqual(exported["schema"], "outside-photo-review/v1")
        self.assertEqual({entry["src"] for entry in exported["flagged"]}, set(PR_SOURCES))
        self.assertEqual(len(exported["flagged"]), 46)
        self.assertTrue(all(entry["reference"] == PR_ID for entry in exported["flagged"]))
        self.assertFalse(any(secret in json.dumps(exported).lower() for secret in ("driveid", "latitude", "longitude", "gps")))
        context.close()

    def test_redacted_full_resolution_sources_paint_at_desktop_and_mobile(self):
        for viewport_name, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
            context = self.browser.new_context(viewport=viewport, reduced_motion="reduce")
            for ref in ("C917", "C918"):
                page = context.new_page()
                index = next(i for i, image in enumerate(PR["images"]) if image["src"].endswith(ref))
                source = PR["images"][index]["src"]
                page.goto(urljoin(BASE_URL, f"#{PR_ID}/{index + 1}"), wait_until="domcontentloaded")
                self.wait_for_painted_source(page, source)
                path = EVIDENCE / f"{viewport_name}-{ref}.png"
                page.screenshot(path=str(path), full_page=False)
                self.assertTrue(path.is_file() and path.stat().st_size > 0)
                page.close()
            context.close()


if __name__ == "__main__":
    unittest.main()
