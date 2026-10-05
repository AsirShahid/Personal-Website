"""Owner-selected Galapagos cover, independent of image order and default opening."""
import json
import os
import subprocess
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
STUDY = "galapagos-2026-january-photos-20261004-20261005-161007"
TORTOISE = "/outside/assets/owner-review/galapagos/G207"


def test_galapagos_key_uses_giant_tortoise_without_changing_default_opening():
    script = """
import fs from 'node:fs';
import {getOutsideStudyCover, getOutsideFirstImageIndex} from './src/utils/outside-place.js';
const data = JSON.parse(fs.readFileSync('src/data/outside-studies.json', 'utf8'));
const study = data.studies.find(s => s.id === process.argv[1]);
console.log(JSON.stringify({cover: getOutsideStudyCover(study).src,
  first: study.images[getOutsideFirstImageIndex(study)].src}));
"""
    result = subprocess.run(["node", "--input-type=module", "-e", script, STUDY], cwd=ROOT, capture_output=True, text=True, check=True)
    observed = json.loads(result.stdout)
    assert observed["cover"] == TORTOISE
    assert observed["first"] == "/outside/assets/owner-review/galapagos/G004"


@pytest.mark.parametrize("width", [390, 1280])
def test_galapagos_cover_paints_in_worklist(width):
    base = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
    with sync_playwright() as pw:
        browser = getattr(pw, os.environ.get("OUTSIDE_BROWSER", "chromium")).launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base, wait_until="domcontentloaded")
            row = page.locator(f'a.oz-row[href="#{STUDY}"]')
            row.scroll_into_view_if_needed()
            image = row.locator("img")
            assert image.get_attribute("src") == TORTOISE + "-s.webp"
            image.evaluate("async im => { if (!im.complete) await new Promise((resolve,reject) => { im.addEventListener('load',resolve,{once:true}); im.addEventListener('error',reject,{once:true}); }); await im.decode(); }")
            assert image.evaluate("im => im.naturalWidth > 0 && im.currentSrc.includes('G207-')")
            evidence = os.environ.get("OUTSIDE_EVIDENCE_DIR")
            if evidence:
                directory = Path(evidence)
                directory.mkdir(parents=True, exist_ok=True)
                row.screenshot(path=str(directory / f"galapagos-key-{width}.png"))
            assert not errors
        finally:
            browser.close()
