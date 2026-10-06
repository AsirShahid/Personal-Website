import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
ROOT = Path(__file__).parents[1]
SOURCE = json.loads((ROOT / "src/data/outside-studies.json").read_text())
LEGACY = json.loads((ROOT / "src/data/outside-legacy-links.json").read_text())
_ASTRO = (ROOT / "src/pages/outside.astro").read_text()
_RULE = re.search(r'cutoff: "([^"]+)",\s*includeStudyIds: \[([^\]]*)\],\s*excludeStudyIds: \[([^\]]*)\]', _ASTRO)
CUTOFF = _RULE.group(1)
INCLUDED_IDS = set(re.findall(r'"([^"]+)"', _RULE.group(2)))
# Owner-requested display hides: still post-cutoff (or an explicit include), now without worklist rows.
EXCLUDED_IDS = set(re.findall(r'"([^"]+)"', _RULE.group(3)))
RECENT_IDS = {
    study["id"] for study in SOURCE["studies"]
    if study["id"] not in EXCLUDED_IDS and (study["id"] in INCLUDED_IDS or (study.get("date") and study["date"] >= CUTOFF))
}


class OutsideRecentAndZoomBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "webkit")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_recent_worklist_is_reversible_without_removing_source_data_or_old_routes(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(BASE_URL, "#new-zealand-2026-july-photos-161007/1"), wait_until="domcontentloaded")
        payload = json.loads(page.locator("#oz-data").text_content() or "{}")
        source_by_id = {study["id"]: study for study in SOURCE["studies"]}
        hidden_studies = [study for study in SOURCE["studies"] if study["id"] not in RECENT_IDS]
        self.assertTrue(all(not study.get("date") or study["date"] < CUTOFF or study["id"] in EXCLUDED_IDS
                            for study in hidden_studies))
        self.assertTrue(any(study["id"] in EXCLUDED_IDS and study.get("date", "") >= CUTOFF for study in hidden_studies),
                        "owner-hidden studies keep post-cutoff dates but must stay off the worklist")
        self.assertTrue(any(not study.get("date") for study in hidden_studies), "undated collection must remain outside recent worklist")
        expected_photos = sum(len(source_by_id[study_id]["images"]) for study_id in RECENT_IDS)
        rows = page.locator(".oz-rows [data-study]")
        visible_ids = [row.get_attribute("href").lstrip("#") for row in rows.all()]
        self.assertEqual(set(visible_ids), RECENT_IDS)
        self.assertIn(f"{len(RECENT_IDS)} studies", page.locator(".oz-topmeta").inner_text().lower())
        self.assertIn(f"{expected_photos} images", page.locator(".oz-topmeta").inner_text().lower())

        # The view is filtered; the embedded payload and every photo record are not.
        source_counts = (len(SOURCE["studies"]), sum(len(study["images"]) for study in SOURCE["studies"]))
        embedded_counts = (len(payload["studies"]), sum(len(study["images"]) for study in payload["studies"]))
        self.assertEqual(embedded_counts, source_counts)
        embedded_by_id = {study["id"]: study for study in payload["studies"]}
        self.assertEqual(set(embedded_by_id), set(source_by_id))
        for study_id, source_study in source_by_id.items():
            self.assertEqual(embedded_by_id[study_id], source_study)
        self.assertEqual(payload["legacy"], LEGACY)

        # Navigation cycles the visible recent worklist, not hidden collections.
        visited = []
        for _ in range(len(visible_ids)):
            visited.append(page.locator("[data-ov=tl]").inner_text().splitlines()[-1])
            page.keyboard.press("n")
        self.assertEqual(len(visited), len(visible_ids))
        positions = [int(item.split("/")[0].split("·")[-1].strip()) for item in visited]
        totals = [int(item.split("/")[-1]) for item in visited]
        self.assertEqual(positions, list(range(1, len(visible_ids) + 1)), visited)
        self.assertEqual(totals, [len(visible_ids)] * len(visible_ids), visited)

        # A pre-cutoff direct route remains source-bound although it is not in rows.
        hidden = next(study for study in SOURCE["studies"] if study["id"] == "orlando-2025-september")
        hidden_page = context.new_page()
        hidden_page.on("pageerror", lambda error: errors.append(str(error)))
        hidden_page.goto(urljoin(BASE_URL, "#orlando-2025-september/1"), wait_until="domcontentloaded")
        hidden_page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.dataset.want?.startsWith(stem); }", arg=hidden["images"][0]["src"])
        self.assertTrue(hidden_page.locator("[data-cells] img").evaluate("(im, stem) => im.dataset.want.startsWith(stem)", hidden["images"][0]["src"]))
        self.assertFalse(hidden_page.locator("[data-route-error]").is_visible())
        self.assertNotIn("#orlando-2025-september", visible_ids)
        self.assertEqual(hidden_page.locator(".oz-row[aria-current=true]").count(), 0,
                         "a directly opened study hidden from the filtered worklist has no current row")

        hidden_page.goto(urljoin(BASE_URL, "#puerto-rico-2025-june/1"), wait_until="domcontentloaded")
        hidden_page.wait_for_function("document.querySelector('[data-ov=tl]')?.textContent?.includes('STUDY')", timeout=10000)
        self.assertFalse(hidden_page.locator("[data-route-error]").is_visible())
        self.assertEqual(hidden_page.locator(".oz-row[aria-current=true]").count(), 0,
                         "an owner-hidden study opens by direct route with no worklist row selected")
        hidden_page.goto(urljoin(BASE_URL, "#puerto-rico-2025-october/1"), wait_until="domcontentloaded")
        hidden_page.wait_for_function("document.querySelector('[data-ov=tl]')?.textContent?.includes('STUDY')", timeout=10000)
        self.assertFalse(hidden_page.locator("[data-route-error]").is_visible())
        self.assertEqual(hidden_page.locator(".oz-row[aria-current=true]").count(), 0,
                         "the second owner-hidden Puerto Rico trip keeps its deep link and no row")
        self.assertNotIn("georgia-2025-october", visible_ids)

        invalid_page = context.new_page()
        invalid_page.on("pageerror", lambda error: errors.append(str(error)))
        invalid_page.goto(urljoin(BASE_URL, "#not-a-supported-study/1"), wait_until="domcontentloaded")
        self.assertTrue(invalid_page.locator("[data-route-error]").is_visible())
        self.assertEqual(errors, [], errors)
        context.close()

    def test_exact_camera_alias_changes_only_the_c887_overlay(self):
        study = next(item for item in SOURCE["studies"] if item["id"] == "puerto-rico-2025-june-photos")
        expected = {"C887": "ONEPLUS 11 5G", "C894": "ONEPLUS 11 5G"}
        errors = []
        for source_suffix, display_label in expected.items():
            with self.subTest(source=source_suffix):
                image = next(item for item in study["images"] if item["src"].endswith(source_suffix))
                ordinal = 1 if source_suffix == "C887" else 2
                context = self.browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(urljoin(BASE_URL, f"#puerto-rico-2025-june/{ordinal}"), wait_until="domcontentloaded")
                page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth>0 && new URL(im.currentSrc).pathname===im.dataset.want && im.dataset.want.startsWith(stem); }", arg=image["src"], timeout=15000)
                raw = next(item for current_study in json.loads(page.locator("#oz-data").text_content() or "{}")["studies"] if current_study["id"] == study["id"] for item in current_study["images"] if item["src"] == image["src"])
                self.assertEqual(raw["cam"], image["cam"])
                self.assertEqual(page.locator('[data-ov="bl"]').inner_text().splitlines()[-1], display_label)
                context.close()
        self.assertEqual(errors, [], errors)

    def test_mobile_history_returns_from_recent_reader_to_worklist_and_forward(self):
        context = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.add_init_script("window.__nativePopStates = []; addEventListener('popstate', event => window.__nativePopStates.push({href: location.href, isTrusted: event.isTrusted}));")
        page.goto(urljoin(BASE_URL, "#montreal-november-2025-photos-20261005/1"), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        page.go_back(wait_until="domcontentloaded", timeout=10000)
        page.wait_for_function("window.__nativePopStates.some(event => event.isTrusted)", timeout=5000)
        page.wait_for_function("!document.body.classList.contains('is-reading')", timeout=5000)
        self.assertEqual(page.evaluate("location.hash"), "")
        self.assertGreater(page.locator(".oz-rows [data-study]").count(), 0)
        page.go_forward(wait_until="domcontentloaded", timeout=10000)
        page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        # The reader rewrites the opened link to the photo's stable id link.
        montreal = next(study for study in SOURCE["studies"] if study["id"] == "montreal-november-2025-photos-20261005")
        self.assertEqual(page.evaluate("location.hash"), f"#{montreal['id']}/{montreal['images'][0]['id']}")
        self.assertTrue(any(event["isTrusted"] for event in page.evaluate("window.__nativePopStates")))
        context.close()


if __name__ == "__main__":
    unittest.main()
