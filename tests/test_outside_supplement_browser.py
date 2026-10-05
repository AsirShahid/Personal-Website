import json
import os
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
EVIDENCE_DIR = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-supplement-browser"))
PARENT_ROUTES = json.loads((Path(__file__).parents[1] / "tests/fixtures/outside-20261004-parent-route-bindings.json").read_text())
SUPPLEMENTS = {
    "montreal-august-2023-photos": {
        "images": 15,
        "unresolved": 1,
    },
    "maryland-national-harbor-2023-august": {
        "images": 1,
        "unresolved": 0,
    },
    "europe-shared-album": {
        "images": 22,
        "unresolved": 17,
    },
    "montreal-november-2025-photos-20261005": {"images": 17, "unresolved": 0},
}


def expected_place_groups(study):
    groups = []
    for index, image in enumerate(study["images"]):
        transit = image.get("transit") is True
        key = ("transit",) if transit else ("place", image.get("d", ""), image.get("place"))
        if not groups or groups[-1]["key"] != key:
            groups.append({"key": key, "start": index, "count": 0, "images": []})
        groups[-1]["count"] += 1
        groups[-1]["images"].append(image)
    next_destination = 1
    for group in groups:
        places = list(dict.fromkeys(image.get("place") or "Location unconfirmed" for image in group["images"]))
        if group["key"][0] == "transit":
            group["displayNumber"] = 0
            group["caption"] = f"Scout · {', '.join(places)}" if places else "Scout"
        else:
            group["displayNumber"] = next_destination
            group["caption"] = " · ".join(places)
            next_destination += 1
    return groups


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

    @staticmethod
    def payload(page):
        return json.loads(page.locator("#oz-data").text_content() or "{}")

    def test_all_supplement_photos_paint_in_desktop_and_mobile(self):
        total_painted = 0
        for study_id, expected in SUPPLEMENTS.items():
            with self.subTest(study=study_id):
                context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
                page = context.new_page()
                js_errors = []
                page.on("pageerror", lambda error: js_errors.append(str(error)))
                page.goto(urljoin(BASE_URL, f"#{study_id}/1"), wait_until="domcontentloaded")
                page.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)
                payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                study = next(s for s in payload["studies"] if s["id"] == study_id)
                self.assertEqual(len(study["images"]), expected["images"])
                self.assertEqual(sum(not image.get("d") for image in study["images"]), expected["unresolved"])
                expected_groups = expected_place_groups(study)
                actual_groups = sorted(study["series"], key=lambda series: series["start"])
                self.assertEqual(
                    [(s["start"], s["count"], s["displayNumber"]) for s in actual_groups],
                    [(g["start"], g["count"], g["displayNumber"]) for g in expected_groups],
                )
                buttons = page.locator("[data-series] .oz-se")
                self.assertEqual(buttons.count(), len(expected_groups))
                visible_labels = [buttons.nth(i).get_attribute("aria-label") for i in range(buttons.count())]
                self.assertTrue(all("undefined" not in (label or "").lower() for label in visible_labels), visible_labels)
                for position, group in enumerate(expected_groups):
                    self.assertTrue((visible_labels[position] or "").startswith(f"Series {group['displayNumber']}, {group['caption']},"), visible_labels[position])
                    self.assertEqual(buttons.nth(position).locator(".oz-se-cap b").inner_text(), f"SE {group['displayNumber']} · {group['caption']}")
                if study_id == "europe-shared-album":
                    self.assertEqual((study.get("date"), study.get("dateEnd")), ("", ""))
                    self.assertEqual(study["place"], "Europe")
                    self.assertTrue(all(image.get("place") == "Location unconfirmed" for image in study["images"] if not image.get("d")))
                    self.assertTrue(all(not image.get("cam") for image in study["images"]))
                if study_id == "montreal-august-2023-photos":
                    for image in study["images"][14:]:
                        self.assertFalse(any(key in image for key in ("d", "t", "tz")))

                for i, item in enumerate(study["images"]):
                    image = page.locator("[data-cells] img").first
                    if i:
                        page.keyboard.press("ArrowRight")
                    expected_stem = item["src"]
                    page.wait_for_function(
                        "stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth > 0 && (im.currentSrc.endsWith(stem + '-m.webp') || im.currentSrc.endsWith(stem + '-l.webp')); }",
                        arg=expected_stem,
                        timeout=10000,
                    )
                    actual = image.get_attribute("src") or ""
                    self.assertTrue(page.evaluate("stem => { const im=document.querySelector('[data-cells] img'); return im && (im.currentSrc.endsWith(stem + '-m.webp') || im.currentSrc.endsWith(stem + '-l.webp')); }", expected_stem), (study_id, i, expected_stem))
                    self.assertRegex(actual, r"-(m|l)\.webp$")
                    self.assertEqual(re.sub(r"-(s|m|l)\.webp$", "", actual), expected_stem)
                    total_painted += 1
                    if i == 0:
                        page.screenshot(path=str(EVIDENCE_DIR / f"desktop-{study_id}.png"), full_page=True)
                    if study_id == "montreal-november-2025-photos-20261005" and "50687dc46ae34c23be92b217abb3de9f" in expected_stem:
                        page.screenshot(path=str(EVIDENCE_DIR / "desktop-montreal-november-snowy-overlook.png"), full_page=True)
                context.close()
                self.assertEqual(js_errors, [], js_errors)

                mobile_errors = []
                mobile = self.browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
                mobile_page = mobile.new_page()
                mobile_page.on("pageerror", lambda error: mobile_errors.append(str(error)))
                mobile_page.goto(urljoin(BASE_URL, f"#{study_id}/1"), wait_until="domcontentloaded")
                mobile_page.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
                mobile_study = next(s for s in json.loads(mobile_page.locator("#oz-data").text_content() or "{}")["studies"] if s["id"] == study_id)
                self.assertEqual(len(mobile_study["images"]), expected["images"])
                mobile_stem = mobile_study["images"][0]["src"]
                mobile_page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth > 0 && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", arg=mobile_stem, timeout=10000)
                self.assertTrue(mobile_page.evaluate("stem => { const im=document.querySelector('[data-cells] img'); return im && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", mobile_stem))
                self.assertTrue(mobile_page.locator("[data-review-flag]").is_visible())
                self.assertLessEqual(mobile_page.evaluate("document.documentElement.scrollWidth"), 390)
                mobile_page.screenshot(path=str(EVIDENCE_DIR / f"mobile-{study_id}.png"), full_page=True)
                mobile.close()
                self.assertEqual(mobile_errors, [], mobile_errors)
        self.assertEqual(total_painted, 55)

    def test_approved_utah_star_photo_paints_on_tablet_at_exact_source(self):
        context = self.browser.new_context(viewport={"width": 768, "height": 1024}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        data = json.loads((Path(__file__).parents[1] / "src/data/outside-studies.json").read_text())
        study = next(s for s in data["studies"] if s["id"] == "american-southwest-2025-october-gallery-20261004-2-20261005")
        image = next(image for image in study["images"] if image["src"] == "/outside/assets/utah-night-sky-2025/utah-night-sky-01")
        ordinal = study["images"].index(image) + 1
        stem = image["src"]
        old_hashes = [route_hash for route_hash, source in PARENT_ROUTES["routes"].items() if source == stem and route_hash.startswith("#american-southwest-2025-october-gallery/")]
        self.assertEqual(len(old_hashes), 1)
        page.goto(urljoin(BASE_URL, f"#american-southwest-2025-october-gallery-20261004-2-20261005/{ordinal}"), wait_until="domcontentloaded")
        page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth > 0 && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", arg=stem, timeout=10000)
        image_element = page.locator("[data-cells] img").first
        self.assertTrue(image_element.is_visible())
        self.assertTrue(page.evaluate("stem => { const im=document.querySelector('[data-cells] img'); return im && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", stem))
        page.goto(urljoin(BASE_URL, old_hashes[0]), wait_until="domcontentloaded")
        page.wait_for_function("stem => { const im=document.querySelector('[data-cells] img'); return im && im.complete && im.naturalWidth > 0 && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", arg=stem, timeout=10000)
        image_element = page.locator("[data-cells] img").first
        self.assertTrue(image_element.is_visible())
        self.assertGreater(image_element.evaluate("im => im.naturalWidth"), 0)
        self.assertTrue(page.evaluate("stem => { const im=document.querySelector('[data-cells] img'); return im && (im.currentSrc.endsWith(stem+'-s.webp') || im.currentSrc.endsWith(stem+'-m.webp') || im.currentSrc.endsWith(stem+'-l.webp')); }", stem))
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 768)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(EVIDENCE_DIR / "tablet-utah-night-sky.png"), full_page=True)
        context.close()
        self.assertEqual(errors, [], errors)

    def test_new_photo_flags_export_exact_source_and_honest_metadata(self):
        for study_id in ("montreal-august-2023-photos", "europe-shared-album", "montreal-november-2025-photos-20261005"):
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
                    "date": "" if study_id == "europe-shared-album" else (study["date"] if study["date"] == study["dateEnd"] else f"{study['date']} to {study['dateEnd'][5:]}"),
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
