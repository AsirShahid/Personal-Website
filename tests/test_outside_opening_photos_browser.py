"""Load-path checks: opening photos warm ahead of time, the desktop landing photo is requested once at the right size,
fonts are preloaded, and no render-blocking asset sits behind a redirect."""
import json
import os
import re
from collections import Counter
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
BASE = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
FULL_SIZE = re.compile(r"(/outside/.+)-(m|l)\.webp$")
DESKTOP = dict(viewport={"width": 1440, "height": 900})
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
SHOWN_SHARP = """want => {
  const im = document.querySelector('[data-cells] .oz-cell img');
  return !!im && im.dataset.want === want && !im.classList.contains('is-proxy') && im.complete && im.naturalWidth > 0;
}"""


def _first_index(study):
    images = study["images"]
    first_se1 = next((i for i, image in enumerate(images) if image.get("se") == 1), -1)
    if first_se1 >= 0:
        return first_se1
    return next((i for i, image in enumerate(images) if not (image.get("transit") is True or image.get("se") == 0)), 0)


def _payload(page):
    return json.loads(page.locator("#oz-data").text_content() or "{}")


def new_url_path(url):
    return re.sub(r"^https?://[^/]+", "", url)


def _openings(page):
    """Recent-worklist opening photo src per study id, in worklist order."""
    payload = _payload(page)
    by_id = {study["id"]: study for study in payload["studies"]}
    return {study_id: by_id[study_id]["images"][_first_index(by_id[study_id])]["src"] for study_id in payload["recentStudyIds"]}


def _track(page):
    seen = {"requested": [], "finished": set(), "redirects": []}

    def path(url):
        match = FULL_SIZE.search(url.split("?")[0])
        return match.group(0) if match else None

    page.on("request", lambda request: path(request.url) and seen["requested"].append(path(request.url)))
    page.on("requestfinished", lambda request: path(request.url) and seen["finished"].add(path(request.url)))
    page.on("response", lambda response: 300 <= response.status < 400 and seen["redirects"].append(response.url))
    return seen


def _wait_until(page, predicate, timeout_ms=30000):
    for _ in range(timeout_ms // 250):
        if predicate():
            return
        page.wait_for_timeout(250)
    raise AssertionError("timed out")


@pytest.fixture()
def browser():
    with sync_playwright() as pw:
        instance = getattr(pw, os.environ.get("OUTSIDE_BROWSER", "chromium")).launch(headless=True)
        try:
            yield instance
        finally:
            instance.close()


def test_every_worklist_study_opens_on_a_photo_that_is_already_loaded(browser):
    context = browser.new_context(**DESKTOP, reduced_motion="reduce")
    page = context.new_page()
    seen = _track(page)
    page.goto(BASE, wait_until="domcontentloaded")
    openings = _openings(page)
    variant = re.search(r"-(?:m|l)\.webp$", page.locator("[data-cells] img").first.get_attribute("data-want") or "").group(0)
    expected = {src + variant for src in openings.values()}
    _wait_until(page, lambda: expected <= seen["finished"])

    # Leave the landing study, then open every other worklist study: each one paints sharp at once, without a
    # second request for its opening photo.
    for row in page.locator(".oz-rows [data-study]").all()[1:]:
        study_id = (row.get_attribute("href") or "").lstrip("#")
        row.click()
        want = openings[study_id] + variant
        state = page.locator("[data-cells] img").first.evaluate("im => ({want: im.dataset.want, proxy: im.classList.contains('is-proxy')})")
        assert state == {"want": want, "proxy": False}, (study_id, state)
        page.wait_for_function(SHOWN_SHARP, arg=want, timeout=2000)
    repeated = {path: count for path, count in Counter(seen["requested"]).items() if path in expected and count > 1}
    assert repeated == {}, repeated
    context.close()


def test_phone_worklist_readies_opening_photos_for_any_card(browser):
    context = browser.new_context(**PHONE, reduced_motion="reduce")
    page = context.new_page()
    seen = _track(page)
    page.goto(BASE, wait_until="domcontentloaded")
    openings = _openings(page)
    expected = {src + "-m.webp" for src in openings.values()}
    _wait_until(page, lambda: expected <= seen["finished"])
    # Openings only: the phone worklist must not start warming whole studies before one is opened.
    opening_srcs = set(openings.values())
    covers = {re.sub(r"-[sml]\.webp$", "", src) for src in page.locator(".oz-rows img").evaluate_all("els => els.map(im => new URL(im.currentSrc || im.src).pathname)")}
    stray = {path for path in seen["requested"] if FULL_SIZE.search(path).group(1) not in opening_srcs | covers}
    assert stray == set(), sorted(stray)[:8]

    row = next(card for card in page.locator(".oz-rows [data-study]").all()
               if re.sub(r"-[sml]\.webp$", "", new_url_path(card.locator("img").evaluate("im => im.currentSrc || im.src"))) != openings[(card.get_attribute("href") or "").lstrip("#")])
    study_id = (row.get_attribute("href") or "").lstrip("#")
    row.click()
    page.wait_for_function("document.body.classList.contains('is-reading')")
    state = page.locator("[data-cells] img").first.evaluate("im => ({want: im.dataset.want, proxy: im.classList.contains('is-proxy')})")
    assert state == {"want": openings[study_id] + "-m.webp", "proxy": False}, state
    context.close()


def test_data_saver_skips_opening_photos(browser):
    context = browser.new_context(**PHONE, reduced_motion="reduce")
    context.add_init_script("Object.defineProperty(Navigator.prototype, 'connection', { configurable: true, get: () => ({ saveData: true }) });")
    page = context.new_page()
    seen = _track(page)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_load_state("load")
    page.wait_for_timeout(2500)
    opening_srcs = set(_openings(page).values())
    covers = {re.sub(r"-[sml]\.webp$", "", src) for src in page.locator(".oz-rows img").evaluate_all("els => els.map(im => new URL(im.currentSrc || im.src).pathname)")}
    warmed = {path for path in seen["requested"] if FULL_SIZE.search(path).group(1) in opening_srcs - covers}
    assert warmed == set(), sorted(warmed)
    context.close()


@pytest.mark.parametrize("width,height,scale,variant", [(1440, 900, 1, "-m"), (1920, 1080, 1, "-l"), (1440, 900, 2, "-l")])
def test_desktop_landing_photo_is_requested_once_at_the_size_it_shows(browser, width, height, scale, variant):
    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale, reduced_motion="reduce")
    page = context.new_page()
    seen = _track(page)
    page.goto(BASE, wait_until="domcontentloaded")
    want = page.locator("[data-cells] img").first.get_attribute("data-want") or ""
    assert want.endswith(variant + ".webp"), want
    page.wait_for_function(SHOWN_SHARP, arg=want, timeout=15000)
    page.wait_for_timeout(500)
    src = want[: -len(variant + ".webp")]
    landing = Counter(path for path in seen["requested"] if FULL_SIZE.search(path).group(1) == src)
    assert landing == Counter({want: 1}), landing
    context.close()


def test_head_preloads_fonts_and_nothing_render_blocking_redirects(browser):
    context = browser.new_context(**DESKTOP, reduced_motion="reduce")
    page = context.new_page()
    seen = _track(page)
    fonts = []
    page.on("request", lambda request: request.resource_type == "font" and fonts.append(request.url))
    page.goto(BASE, wait_until="load")
    preloads = page.locator('link[rel="preload"][as="font"]').evaluate_all("els => els.map(el => new URL(el.href).pathname)")
    assert len(preloads) == 2 and all(p.startswith("/_astro/") and p.endswith(".woff2") for p in preloads), preloads
    page.wait_for_timeout(500)
    used = {re.sub(r"^https?://[^/]+", "", url) for url in fonts}
    assert set(preloads) <= used, (preloads, used)
    blocking = page.locator('link[rel="stylesheet"]').evaluate_all("els => els.map(el => el.getAttribute('href'))")
    assert blocking and all("@" not in href for href in blocking), blocking
    assert [url for url in seen["redirects"] if "/_astro/" in url] == []
    context.close()
