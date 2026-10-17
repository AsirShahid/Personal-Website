"""Opening a study warms every photo in the background, so the first pass through it is as sharp as the second."""
import json
import os
import re
from collections import Counter
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
BASE = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
FULL_SIZE = re.compile(r"(/outside/.+)-(?:m|l)\.webp$")
STUDY_OF_SRC = {image["src"]: study["id"] for study in DATA["studies"] for image in study["images"]}
PROFILES = {
    "desktop": dict(viewport={"width": 1280, "height": 900}),
    "phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True),
}
SHOWN_SHARP = """want => {
  const im = document.querySelector('[data-cells] .oz-cell img');
  return !!im && im.dataset.want === want && !im.classList.contains('is-proxy') && im.complete && im.naturalWidth > 0
    && new URL(im.currentSrc).pathname === want;
}"""


def _smallest_study(minimum):
    return min((s for s in DATA["studies"] if len(s["images"]) >= minimum), key=lambda s: len(s["images"]))


def _track_full_size(page):
    seen = {"requested": [], "finished": set()}

    def path(url):
        match = FULL_SIZE.search(url.split("?")[0])
        return match.group(0) if match else None

    page.on("request", lambda request: path(request.url) and seen["requested"].append(path(request.url)))
    page.on("requestfinished", lambda request: path(request.url) and seen["finished"].add(path(request.url)))
    return seen


def _wanted_variant(page):
    return re.search(r"-(?:m|l)\.webp$", page.locator("[data-cells] .oz-cell img").first.get_attribute("data-want") or "").group(0)


def _wait_until(page, predicate, timeout=30000):
    deadline = timeout / 250
    while not predicate():
        deadline -= 1
        assert deadline > 0, "timed out"
        page.wait_for_timeout(250)


@pytest.fixture()
def browser():
    with sync_playwright() as pw:
        instance = getattr(pw, os.environ.get("OUTSIDE_BROWSER", "chromium")).launch(headless=True)
        try:
            yield instance
        finally:
            instance.close()


@pytest.mark.parametrize("profile", PROFILES)
def test_opening_a_study_warms_every_photo_so_the_first_pass_is_sharp(browser, profile):
    study = _smallest_study(6)
    context = browser.new_context(**PROFILES[profile], reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    seen = _track_full_size(page)
    page.goto(BASE + f"#{study['id']}/{study['images'][0]['id']}", wait_until="domcontentloaded")
    if profile == "phone":
        page.wait_for_function("document.body.classList.contains('is-reading')")
    variant = _wanted_variant(page)
    expected = {image["src"] + variant for image in study["images"]}
    page.wait_for_function(SHOWN_SHARP, arg=study["images"][0]["src"] + variant, timeout=15000)

    # Every photo in the study is fetched at the size the reader shows, without the reader moving.
    _wait_until(page, lambda: expected <= seen["finished"])
    page.wait_for_timeout(300)  # the page's onload for the last response lands just after the network event

    # Stepping through the study for the first time never falls back to the blurry thumbnail.
    for image in study["images"][1:]:
        page.keyboard.press("ArrowDown")
        want = image["src"] + variant
        state = page.locator("[data-cells] .oz-cell img").first.evaluate("im => ({want: im.dataset.want, proxy: im.classList.contains('is-proxy')})")
        assert state == {"want": want, "proxy": False}, state
        page.wait_for_function(SHOWN_SHARP, arg=want, timeout=1000)
    assert errors == []
    context.close()


def test_phone_worklist_does_not_warm_a_study_until_it_is_opened(browser):
    context = browser.new_context(**PROFILES["phone"], reduced_motion="reduce")
    page = context.new_page()
    seen = _track_full_size(page)
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    # Only the worklist cards' own cover images may load at full size while the list is showing.
    per_study = Counter(STUDY_OF_SRC.get(FULL_SIZE.search(path).group(1)) for path in seen["requested"])
    assert max(per_study.values(), default=0) <= 1, per_study

    row = page.locator(".oz-rows [data-study]").first
    study = next(s for s in DATA["studies"] if s["id"] == (row.get_attribute("href") or "").lstrip("#"))
    row.click()
    page.wait_for_function("document.body.classList.contains('is-reading')")
    expected = {image["src"] + _wanted_variant(page) for image in study["images"]}
    _wait_until(page, lambda: expected <= seen["finished"])
    context.close()


def test_data_saver_keeps_the_neighbour_window_only(browser):
    study = _smallest_study(12)
    context = browser.new_context(**PROFILES["desktop"], reduced_motion="reduce")
    context.add_init_script("Object.defineProperty(Navigator.prototype, 'connection', { configurable: true, get: () => ({ saveData: true }) });")
    page = context.new_page()
    seen = _track_full_size(page)
    page.goto(BASE + f"#{study['id']}/{study['images'][0]['id']}", wait_until="domcontentloaded")
    variant = _wanted_variant(page)
    page.wait_for_function(SHOWN_SHARP, arg=study["images"][0]["src"] + variant, timeout=15000)
    page.wait_for_timeout(2500)
    fetched = {path for path in seen["requested"] if STUDY_OF_SRC.get(FULL_SIZE.search(path).group(1)) == study["id"]}
    # The opening photo plus the existing look-ahead neighbours, never the rest of the study.
    assert fetched <= {image["src"] + variant for image in study["images"][:6]}, sorted(fetched)
    context.close()
