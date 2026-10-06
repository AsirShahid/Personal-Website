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
CANONICAL = re.compile(r"^UTC[+-]\d{2}:\d{2}$")
SPELLING = re.compile(r"^UTC([+-])(\d{1,2})(?::(\d{2}))?$")


def canonical(value):
    """The single display shape the overlay must use, mirroring src/utils/outside-tz.js."""
    if not isinstance(value, str) or not value.strip():
        return ""
    match = SPELLING.fullmatch(value.strip().upper())
    if not match:
        return value.strip()
    hours, minutes = match.group(2), match.group(3)
    return f"UTC{match.group(1)}{hours.zfill(2)}:{minutes or '00'}"


def zone_of(study, image):
    return image.get("tz") or study.get("tz") or ""


def differing_images(study):
    """Images whose stored zone spelling is not yet the canonical display shape."""
    return [(ordinal, image) for ordinal, image in enumerate(study["images"], 1)
            if zone_of(study, image) and zone_of(study, image) != canonical(zone_of(study, image))]


class OutsideTimezoneOverlayBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "webkit")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def zone_lines(self, page):
        texts = page.locator("[data-ov=tr] > div").all_inner_texts()
        return [text.strip() for text in texts if text.strip().upper().startswith("UTC")]

    def test_mixed_spellings_render_one_canonical_zone_while_stored_records_stay_intact(self):
        mixed = [study for study in SOURCE["studies"] if differing_images(study)]
        # The owner's complaint: one study showing both "UTC+2" and "UTC+02:00" over its own photos.
        self.assertTrue(any(study["id"] == "pakistan-2026-summer-gallery-20261005" for study in mixed))
        self.assertGreater(len(mixed), 1)

        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        try:
            for study in mixed:
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                payload = None
                for ordinal, image in differing_images(study):
                    page.goto(urljoin(BASE_URL, f"#{study['id']}/{ordinal}"), wait_until="domcontentloaded")
                    if payload is None:
                        payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                    expected = canonical(zone_of(study, image))
                    zones = self.zone_lines(page)
                    self.assertEqual(zones, [expected], f"{study['id']} image {ordinal}")
                    self.assertRegex(zones[0], CANONICAL, f"{study['id']} image {ordinal}")
                self.assertEqual(errors, [])

                # Display-only fix: the embedded records keep their original stored strings.
                compiled = next(item for item in payload["studies"] if item["id"] == study["id"])
                self.assertEqual([item.get("tz") for item in compiled["images"]],
                                 [item.get("tz") for item in study["images"]])
                page.close()
        finally:
            context.close()

    def test_unknown_zone_stays_absent_and_known_zone_shows_canonical_shape(self):
        context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        try:
            page = context.new_page()
            undated = next(study for study in SOURCE["studies"]
                           if all(not zone_of(study, image) for image in study["images"]))
            page.goto(urljoin(BASE_URL, f"#{undated['id']}/1"), wait_until="domcontentloaded")
            self.assertEqual(self.zone_lines(page), [], "no stored zone must not invent one")

            known = next(study for study in SOURCE["studies"]
                         if any(CANONICAL.fullmatch(zone_of(study, image)) for image in study["images"]))
            ordinal = next(index for index, image in enumerate(known["images"], 1)
                           if CANONICAL.fullmatch(zone_of(known, image)))
            page.goto(urljoin(BASE_URL, f"#{known['id']}/{ordinal}"), wait_until="domcontentloaded")
            self.assertEqual(self.zone_lines(page), [zone_of(known, known["images"][ordinal - 1])])
        finally:
            context.close()
