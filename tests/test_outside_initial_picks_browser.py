"""Initial selections are labeled per photo without changing owner removal flags."""
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.environ.get('OUTSIDE_CANDIDATE_URL', 'http://127.0.0.1:4321/outside/')
SOURCE = json.loads((Path(__file__).parents[1] / 'src/data/outside-studies.json').read_text())
STUDY = next(s for s in SOURCE['studies'] if s['id'] == 'colorado-2025-june')


def test_initial_pick_labels_follow_photo_identity_and_leave_flags_independent():
    with sync_playwright() as p:
        browser = getattr(p, os.environ.get('OUTSIDE_BROWSER', 'chromium')).launch()
        for width in (390, 1440):
            context = browser.new_context(viewport={'width': width, 'height': 900})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # Owner curation can remove a pick; exercise a retained marker, not a frozen source.
            initial_pick = next(image for image in STUDY['images'] if image.get('initialPick'))
            page.goto(BASE_URL + '?review#' + STUDY['id'] + '/' + initial_pick['id'])
            overlay = page.locator('[data-ov=tr]')
            expect(overlay).to_contain_text('INITIAL PICK')
            flag = page.locator('[data-review-flag]')
            expect(flag).to_have_attribute('aria-pressed', 'false')
            flag.click()
            expect(overlay).to_contain_text('INITIAL PICK')
            expect(flag).to_have_attribute('aria-pressed', 'true')
            flag.click()
            for image in STUDY['images']:
                page.evaluate('(hash) => { location.hash = hash; }', '#' + STUDY['id'] + '/' + image['id'])
                page.wait_for_function('(src) => document.querySelector("[data-cells] img")?.dataset.want?.startsWith(src)', arg=image['src'])
                assert ('INITIAL PICK' in overlay.inner_text()) == bool(image.get('initialPick'))
                expect(flag).to_have_attribute('aria-pressed', 'false')
            assert not errors
            context.close()
        browser.close()
