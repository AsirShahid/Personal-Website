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
PR_ID = "puerto-rico-2025-june-photos"
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

    def test_compiled_recent_inventory_and_all_25_photo_sources_paint_and_decode(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, f"#{PR_ID}/1"), wait_until="domcontentloaded")
        payload = json.loads(page.locator("#oz-data").text_content() or "{}")
        self.assertEqual((len(payload["studies"]), sum(len(study["images"]) for study in payload["studies"])), (21, 414))
        visible = page.locator(".oz-rows [data-study]")
        visible_ids = [(row.get_attribute("href") or "").lstrip("#") for row in visible.all()]
        self.assertEqual((len(visible_ids), sum(len(study["images"]) for study in SOURCE["studies"] if study["id"] in visible_ids)), (6, 233))
        self.assertNotIn(PR_ID, visible_ids)
        self.assertNotIn("puerto-rico-2025-october", visible_ids)
        self.assertNotIn("georgia-2025-october", visible_ids)
        self.assertIn("6 studies", page.locator(".oz-topmeta").inner_text().lower())
        self.assertIn("233 images", page.locator(".oz-topmeta").inner_text().lower())

        painted = []
        for ordinal, image in enumerate(PR["images"], 1):
            page.goto(urljoin(BASE_URL, f"#{PR_ID}/{ordinal}"), wait_until="domcontentloaded")
            result = self.wait_for_painted_source(page, image["src"])
            self.assertTrue(re.search(r"-(s|m|l)\.webp$", result["current"]))
            painted.append(image["src"])
        self.assertEqual(painted, PR_SOURCES)
        self.assertEqual(len(painted), 25)

        # Explicit /N keeps the historical source; a valid bare alias resolves to its target study's first SE1.
        old_alias = payload["aliases"][OLD_ID]
        alias_targets = old_alias.get("targets", [])
        default_target = old_alias.get("defaultTarget") if "defaultTarget" in old_alias else next((row for row in alias_targets if row is not None), None) if isinstance(alias_targets, list) else None
        target_study = next((study for study in payload["studies"] if isinstance(default_target, dict) and study["id"] == default_target.get("studyId")), None)
        target_index = default_target.get("index") if isinstance(default_target, dict) else None
        valid_default = target_study and isinstance(target_index, int) and not isinstance(target_index, bool) and 0 <= target_index < len(target_study["images"])
        first_se1 = next((image["src"] for image in target_study["images"] if image.get("se") == 1), None) if valid_default else None
        self.assertIsNotNone(first_se1)
        for route, expected in ((f"#{OLD_ID}", first_se1), (f"#{OLD_ID}/1", "/outside/assets/owner-review/core-trips/C887"), (f"#{OLD_ID}/2", "/outside/assets/owner-review/core-trips/C894")):
            page.goto(urljoin(BASE_URL, route), wait_until="domcontentloaded")
            result = self.wait_for_painted_source(page, expected)
            self.assertEqual(re.sub(r"-(?:s|m|l)\.webp$", "", result["want"]), expected, route)
        page.goto(urljoin(BASE_URL, "#puerto-rico-2025-october/1"), wait_until="domcontentloaded")
        historical = next(study for study in SOURCE["studies"] if study["id"] == "puerto-rico-2025-october")
        self.assertTrue(self.wait_for_painted_source(page, historical["images"][0]["src"])["want"].startswith(historical["images"][0]["src"]))
        self.assertEqual(errors, [], errors)
        context.close()

    def test_redacted_full_resolution_sources_paint_at_desktop_and_mobile(self):
        for viewport_name, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
            context = self.browser.new_context(viewport=viewport, reduced_motion="reduce")
            for ref in ("C917", "C919"):
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
