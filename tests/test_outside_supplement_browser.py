import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE_DIR = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-supplement-browser"))
SUPPLEMENTS = {
    "montreal-august-2023-review-supplement": {
        "images": 20,
        "series": 4,
        "unresolved": 8,
        "series_titles": ["2023-08-06", "2023-08-07", "2023-08-08", "Capture time unresolved"],
    },
    "unsorted-august-2023-review-supplement": {
        "images": 3,
        "series": 2,
        "unresolved": 0,
        "series_titles": ["2023-08-08", "2023-08-13"],
    },
    "europe-shared-album": {
        "images": 22,
        "series": 2,
        "unresolved": 17,
        "series_titles": ["EXIF date: February 19, 2023", "Date unknown"],
    },
}


class OutsideSupplementBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(headless=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_all_supplement_photos_paint_in_desktop_and_mobile(self):
        total_painted = 0
        for study_id, expected in SUPPLEMENTS.items():
            with self.subTest(study=study_id):
                context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
                page = context.new_page()
                page.goto(urljoin(BASE_URL, f"#{study_id}/1"), wait_until="domcontentloaded")
                page.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)
                payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                study = next(s for s in payload["studies"] if s["id"] == study_id)
                self.assertEqual(len(study["images"]), expected["images"])
                self.assertEqual(len(study["series"]), expected["series"])
                self.assertEqual([s["title"] for s in study["series"]], expected["series_titles"])
                self.assertEqual(sum(not image.get("d") for image in study["images"]), expected["unresolved"])
                buttons = page.locator("[data-series] .oz-se")
                self.assertEqual(buttons.count(), expected["series"])
                visible_labels = [buttons.nth(i).get_attribute("aria-label") for i in range(buttons.count())]
                self.assertTrue(all("undefined" not in (label or "").lower() for label in visible_labels), visible_labels)
                for title in expected["series_titles"]:
                    self.assertTrue(any(title in label for label in visible_labels), title)
                if study_id == "europe-shared-album":
                    self.assertEqual(study.get("date"), "")
                    self.assertEqual(study.get("dateEnd"), "")
                    self.assertEqual(study["place"], study["region"])
                    self.assertTrue(all(not image.get("cam") for image in study["images"]))
                if study_id == "montreal-august-2023-review-supplement":
                    for image in study["images"][12:]:
                        self.assertFalse(any(key in image for key in ("d", "t", "tz")))

                for i, item in enumerate(study["images"]):
                    image = page.locator("[data-cells] img").first
                    if i:
                        page.keyboard.press("ArrowRight")
                    expected_stem = item["src"]
                    page.wait_for_function(
                        "([stem]) => { const im=document.querySelector('[data-cells] img'); const src=im?.getAttribute('src') || ''; return im && im.complete && im.naturalWidth > 0 && (src === stem + '-m.webp' || src === stem + '-l.webp'); }",
                        arg=[expected_stem],
                        timeout=10000,
                    )
                    actual = image.get_attribute("src") or ""
                    self.assertRegex(actual, r"-(m|l)\.webp$")
                    self.assertEqual(re.sub(r"-(s|m|l)\.webp$", "", actual), expected_stem)
                    total_painted += 1
                    if i == 0:
                        page.screenshot(path=str(EVIDENCE_DIR / f"desktop-{study_id}.png"), full_page=True)
                context.close()

                mobile = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
                mobile_page = mobile.new_page()
                mobile_page.goto(urljoin(BASE_URL, f"#{study_id}/1"), wait_until="domcontentloaded")
                mobile_page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
                mobile_page.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)
                mobile_study = next(s for s in json.loads(mobile_page.locator("#oz-data").text_content() or "{}")["studies"] if s["id"] == study_id)
                self.assertEqual(len(mobile_study["images"]), expected["images"])
                self.assertTrue(mobile_page.locator("[data-review-flag]").is_visible())
                mobile_page.screenshot(path=str(EVIDENCE_DIR / f"mobile-{study_id}.png"), full_page=True)
                mobile.close()
        self.assertEqual(total_painted, 45)

    def test_new_photo_flags_export_exact_source_and_honest_metadata(self):
        for study_id in ("montreal-august-2023-review-supplement", "europe-shared-album"):
            with self.subTest(study=study_id):
                context = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
                page = context.new_page()
                page.goto(urljoin(BASE_URL, f"#{study_id}/1"), wait_until="domcontentloaded")
                page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
                page.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)
                payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                study = next(s for s in payload["studies"] if s["id"] == study_id)
                expected = {
                    "src": study["images"][0]["src"],
                    "studyLabel": study["place"],
                    "date": "" if study_id == "europe-shared-album" else "2023-08-06 to 08-08",
                    "reference": study_id,
                }
                page.locator("[data-review-flag]").click()
                self.assertEqual(page.locator("[data-review-flag]").get_attribute("aria-pressed"), "true")
                self.assertEqual(page.locator("[data-review-count]").inner_text(), "1 flagged")
                stored = page.evaluate("JSON.parse(localStorage.getItem('outside-studies:photo-review:v1'))")
                self.assertEqual(stored["flaggedSrcs"], [expected["src"]])
                with page.expect_download(timeout=5000) as download_info:
                    page.locator("[data-review-export]").click()
                export = json.loads(Path(download_info.value.path()).read_text())
                self.assertEqual(export["schema"], "outside-photo-review/v1")
                self.assertEqual(export["flagged"], [expected])
                context.close()


if __name__ == "__main__":
    unittest.main()
