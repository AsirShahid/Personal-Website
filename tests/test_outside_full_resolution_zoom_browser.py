"""Zooming a photo that has a full-resolution copy (-x.webp) swaps it in; fit-size views never fetch it."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('OUTSIDE_CANDIDATE_URL', 'http://127.0.0.1:4321/outside/')
SOURCE = json.loads((Path(__file__).parents[1] / 'src/data/outside-studies.json').read_text())
# Any retained marked photo with a neighbour; owner cuts may remove a particular one, so nothing is hardcoded.
MARKED = next((s, k) for s in SOURCE['studies'] for k, im in enumerate(s['images'][:-1]) if im.get('xl') and s['images'][k + 1].get('xl'))
UNMARKED = next(((s, k) for s in SOURCE['studies'] for k, im in enumerate(s['images']) if not im.get('xl')), None)

STATE = """() => { const im = document.querySelector('[data-cells] .oz-cell img');
  return { current: new URL(im.currentSrc || im.src, location.href).pathname, want: im.dataset.want,
           natural: im.naturalWidth, complete: im.complete, scale: new DOMMatrixReadOnly(getComputedStyle(im).transform).a }; }"""


def open_photo(page, study, k):
    image = study['images'][k]
    page.goto(BASE_URL + '#' + study['id'] + '/' + image['id'], wait_until='domcontentloaded')
    page.wait_for_function("""() => { const im = document.querySelector('[data-cells] img');
        return im?.complete && im.naturalWidth > 0 && new URL(im.currentSrc).pathname === im.dataset.want; }""", timeout=20000)
    return image


def test_zoom_swaps_in_the_full_resolution_copy_and_fit_size_never_requests_it():
    study, k = MARKED
    with sync_playwright() as p:
        browser = getattr(p, os.environ.get('OUTSIDE_BROWSER', 'chromium')).launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        errors, full_requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda r: full_requests.append(r.url) if r.url.endswith('-x.webp') else None)
        image = open_photo(page, study, k)
        state = page.evaluate(STATE)
        assert state['current'].endswith(('-m.webp', '-l.webp')), state
        page.wait_for_timeout(1500)  # the study warms in the background; it must not fetch full-resolution copies
        assert full_requests == [], full_requests
        for _ in range(3):
            page.keyboard.press('+')  # 1.25 ** 3 = 1.95 > 1.5
        page.wait_for_function("(src) => new URL(document.querySelector('[data-cells] .oz-cell img').currentSrc).pathname === src + '-x.webp'",
                               arg=image['src'], timeout=20000)
        state = page.evaluate(STATE)
        assert state['natural'] == image['w'] and state['scale'] > 1.5, (state, image['w'])
        assert len(full_requests) == 1 and full_requests[0].endswith(image['src'].lstrip('/').split('/', 1)[1] + '-x.webp'), full_requests
        page.locator('[data-fit]').click()  # Fit resets geometry only; the sharp frame stays while the photo is open
        state = page.evaluate(STATE)
        assert abs(state['scale'] - 1) < 0.01 and state['current'].endswith('-x.webp'), state
        page.keyboard.press('ArrowRight')  # the next photo opens at fit size again, with no full-resolution request
        page.wait_for_function("(src) => document.querySelector('[data-cells] .oz-cell img').dataset.want.startsWith(src)",
                               arg=study['images'][k + 1]['src'], timeout=20000)
        page.wait_for_function("""() => { const im = document.querySelector('[data-cells] img'); return im.complete && new URL(im.currentSrc).pathname === im.dataset.want; }""", timeout=20000)
        state = page.evaluate(STATE)
        assert state['current'].endswith(('-m.webp', '-l.webp')), state
        assert len(full_requests) == 1, full_requests
        assert not errors, errors
        context.close()
        browser.close()


def test_photos_without_a_full_resolution_copy_never_request_one():
    if UNMARKED is None:
        return
    study, k = UNMARKED
    with sync_playwright() as p:
        browser = getattr(p, os.environ.get('OUTSIDE_BROWSER', 'chromium')).launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        requests = []
        page.on('request', lambda r: requests.append(r.url) if r.url.endswith('-x.webp') else None)
        open_photo(page, study, k)
        for _ in range(4):
            page.keyboard.press('+')
        page.wait_for_function("() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('[data-cells] .oz-cell img')).transform).a > 1.5")
        page.wait_for_timeout(1000)
        assert requests == [], requests
        assert page.evaluate(STATE)['current'].endswith(('-m.webp', '-l.webp'))
        context.close()
        browser.close()
