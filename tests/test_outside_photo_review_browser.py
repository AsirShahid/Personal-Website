"""Owner review flags survive navigation/reloads and export exact source identities."""
import json
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('OUTSIDE_CANDIDATE_URL', 'http://127.0.0.1:4321/outside/')
SOURCE = json.loads((Path(__file__).parents[1] / 'src/data/outside-studies.json').read_text())
STUDY = next(s for s in SOURCE['studies'] if s['id'] == 'colorado-2025-june-gallery')
KEY = 'outside-studies:photo-review:v1'

class PhotoReviewTests(unittest.TestCase):
    def test_flag_persists_and_exports_exact_source_without_removing_it(self):
        with sync_playwright() as p:
            browser = getattr(p, os.environ.get('OUTSIDE_BROWSER', 'chromium')).launch()
            for width in (390, 1440):
                with self.subTest(width=width):
                    context = browser.new_context(viewport={'width': width, 'height': 900}, accept_downloads=True)
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    first, second = STUDY['images'][:2]
                    url = BASE_URL + '#' + STUDY['id'] + '/' + first['id']
                    page.goto(url, wait_until='domcontentloaded')
                    button = page.locator('[data-review-flag]')
                    self.assertEqual(button.count(), 1, 'Flag photo control must be restored')
                    button.click()
                    self.assertEqual(button.get_attribute('aria-pressed'), 'true')
                    stored = page.evaluate('(key) => JSON.parse(localStorage.getItem(key))', KEY)
                    self.assertEqual(stored['flaggedSrcs'], [first['src']])
                    page.goto(BASE_URL + '#' + STUDY['id'] + '/' + second['id'])
                    self.assertEqual(button.get_attribute('aria-pressed'), 'false')
                    page.goto(url)
                    page.reload()
                    self.assertEqual(button.get_attribute('aria-pressed'), 'true')
                    with page.expect_download() as download:
                        page.locator('[data-review-export]').click()
                    payload = json.loads(Path(download.value.path()).read_text())
                    self.assertEqual(payload['schema'], 'outside-photo-review/v1')
                    self.assertEqual([r['src'] for r in payload['flagged']], [first['src']])
                    self.assertEqual(payload['flagged'][0]['photoId'], first['id'])
                    self.assertTrue(payload['flagged'][0]['url'].endswith('/' + first['id']))
                    page.wait_for_function('(src) => { const im=document.querySelector("[data-cells] img"); return im?.complete && im.naturalWidth > 0 && im.dataset.want?.startsWith(src); }', arg=first['src'])
                    button.click()
                    self.assertEqual(button.get_attribute('aria-pressed'), 'false')
                    self.assertEqual(page.evaluate('(key) => JSON.parse(localStorage.getItem(key)).flaggedSrcs', KEY), [])
                    self.assertEqual(errors, [])
                    context.close()
            browser.close()
