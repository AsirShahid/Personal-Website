"""Real-payload area worklist and series-strip acceptance.

No route interception or payload injection is used here. Every browser assertion
reads the served #oz-data and compares it to the repository payload.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:8770/outside/")
BROWSER_NAME = os.environ.get("OUTSIDE_BROWSER", "webkit").lower()
EVIDENCE_DIR = Path(os.environ.get("OUTSIDE_AREA_EVIDENCE_DIR") or tempfile.mkdtemp(prefix="outside-area-acceptance-"))

TARGET_PREFIXES = {
    "new_zealand": "new-zealand-2026-july",
    "australia": "australia-2026-july",
    "pakistan": "pakistan-2026-summer",
    "galapagos": "galapagos-2026-january",
    "montreal": "montreal-november-2025",
    "southwest": "american-southwest-2025-october-gallery",
}
EXPECTED_AREA_ORDER = {
    "new_zealand": ["Auckland", "Rotorua"],
    "australia": ["Bangkok", "South West", "Rottnest Island", "Perth"],
    "pakistan": ["Rome", "Tirana", "Karachi", "Islamabad", "Murree", "Lahore"],
    "galapagos": ["Santa Cruz", "Isabela", "San Cristóbal"],
    "montreal": ["Montréal"],
    "southwest": ["Joshua Tree", "Las Vegas", "Grand Canyon", "Zion", "Hoover Dam"],
}
AREA_BY_PLACE = {
    "new_zealand": {"Waiotapu": "Rotorua"},
    "australia": {
        "Busselton": "South West", "Dunsborough": "South West", "Yallingup": "South West",
        "Margaret River": "South West", "Augusta": "South West", "Hamelin Bay": "South West",
        "Fremantle": "Perth",
    },
    "pakistan": {"Albania": "Tirana", "Nathia Gali": "Murree"},
}
# Landscape widths include the narrowest desktop layout (900px media-query
# breakpoint + 1), the required iPad landscape widths, and the 375px phone.
VIEWPORTS = ((375, 812), (901, 820), (1024, 768), (1180, 820), (1194, 834), (1366, 1024))
STRIP_VIEWPORT_WIDTHS = (375, 901, 1024, 1180, 1194, 1366)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def unique(values):
    return list(dict.fromkeys(value for value in values if isinstance(value, str) and value.strip()))


def is_transit(image: dict) -> bool:
    return image.get("transit") is True or image.get("se") == 0


def _focus_studies(data: dict) -> dict[str, dict | None]:
    studies = data.get("studies", [])
    return {
        key: next((study for study in studies if str(study.get("id", "")).startswith(prefix)), None)
        for key, prefix in TARGET_PREFIXES.items()
    }


def _ordered_areas(study: dict, transit_value: bool) -> list[str]:
    images = study.get("images", [])
    if transit_value:
        return unique(image.get("area") for image in images if is_transit(image))
    observed = {image.get("area") for image in images if not is_transit(image)}
    return [area for area in study.get("areaOrder", []) if area in observed]


def _worklist_area_line(study: dict) -> str:
    ordinary = _ordered_areas(study, False)
    transits = _ordered_areas(study, True)
    if len(ordinary) == 1 and ordinary[0] == study.get("place") and study.get("country"):
        ordinary = [study["country"]]
    text = " · ".join(ordinary) if ordinary else "Location unconfirmed"
    if transits:
        text += " · via " + ", ".join(transits)
    return text


def _expected_area(key: str, image: dict) -> str:
    return AREA_BY_PLACE.get(key, {}).get(image.get("place"), image.get("place", ""))


def _expected_area_order(key: str, study: dict) -> list[str]:
    # Configuration retains the complete owner list; rendering filters it to
    # actual photographs, independently checked by worklist/series assertions.
    return EXPECTED_AREA_ORDER[key]


def _short_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{MONTHS[parsed.month - 1]} {parsed.day}"


class AcceptanceEvidence:
    def __init__(self):
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE_DIR / "area-acceptance.json"
        self.report = {
            "schema": "outside-area-strip-real-acceptance-v1",
            "status": "INCOMPLETE",
            "candidate_url": BASE_URL,
            "browser": BROWSER_NAME,
            "source_path": str(DATA_PATH),
            "source_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
            "viewports": [{"width": width, "height": height} for width, height in VIEWPORTS],
            "checks": [],
            "screenshots": [],
            "page_errors": [],
        }
        self.failures = []
        self.write()

    def write(self):
        temp = self.path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + "\n")
        temp.replace(self.path)

    def check(self, check_id: str, passed: bool, details=None):
        row = {"id": check_id, "status": "PASS" if passed else "FAIL", "details": details}
        self.report["checks"].append(row)
        if not passed:
            self.failures.append(row)
        self.write()

    def screenshot(self, page, relative_path: str):
        target = EVIDENCE_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target), full_page=True, animations="disabled")
        self.report["screenshots"].append({"path": str(target), "bytes": target.stat().st_size})
        self.write()

    def finish(self):
        self.report["status"] = "FAIL" if self.failures else "PASS"
        self.report["failure_count"] = len(self.failures)
        self.report["failed_checks"] = self.failures
        self.write()
        assert not self.failures, f"Area/strip real-payload acceptance failed; see {self.path} ({len(self.failures)} failed checks)"


def _unclamped_measurement(page, row) -> dict:
    return row.locator(".oz-region").evaluate("""async el => {
      await document.fonts.ready;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const clone = el.cloneNode(true);
      clone.dataset.acceptanceUnclampedClone = 'true';
      Object.assign(clone.style, {
        position: 'fixed', left: '-10000px', top: '0', visibility: 'hidden',
        display: 'block', width: `${r.width}px`, boxSizing: 'border-box',
        height: 'auto', minHeight: '0', maxHeight: 'none', overflow: 'visible',
        whiteSpace: 'normal', webkitLineClamp: 'unset', webkitBoxOrient: 'initial',
        contain: 'none', transform: 'none'
      });
      el.parentElement.append(clone);
      try {
        const natural = clone.getBoundingClientRect();
        return {
          width: r.width, visibleHeight: r.height, visibleClientHeight: el.clientHeight,
          lineHeight: parseFloat(cs.lineHeight), lineClamp: cs.webkitLineClamp,
          naturalHeight: natural.height, naturalScrollHeight: clone.scrollHeight,
          naturalClientHeight: clone.clientHeight, naturalScrollWidth: clone.scrollWidth,
          naturalClientWidth: clone.clientWidth,
          twoLineLimit: parseFloat(cs.lineHeight) * 2,
          text: el.textContent.trim()
        };
      } finally {
        clone.remove();
      }
    }""")


def _check_real_payload(source: dict, runtime: dict, evidence: AcceptanceEvidence):
    source_base = {key: source.get(key) for key in ("studies", "aliases")}
    runtime_base = {key: runtime.get(key) for key in ("studies", "aliases")}
    if isinstance(source_base.get("studies"), list):
        source_base["studies"] = sorted(source_base["studies"], key=lambda study: study.get("id", ""))
    if isinstance(runtime_base.get("studies"), list):
        runtime_base["studies"] = sorted(runtime_base["studies"], key=lambda study: study.get("id", ""))
    same = json.dumps(source_base, ensure_ascii=False, sort_keys=True, separators=(",", ":")) == json.dumps(runtime_base, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    evidence.check("browser.real-payload-matches-source", same, {
        "source_studies": len(source_base.get("studies") or []),
        "runtime_studies": len(runtime_base.get("studies") or []),
        "source_aliases": len(source_base.get("aliases") or {}),
        "runtime_aliases": len(runtime_base.get("aliases") or {}),
    })


def _check_strip(page, study: dict, evidence: AcceptanceEvidence, width: int):
    ordered = sorted(study.get("series", []), key=lambda row: row.get("start", -1))
    buttons = page.locator("[data-series] [data-se]")
    evidence.check(f"strip.series-count.{width}", buttons.count() == len(ordered), {
        "buttons": buttons.count(), "series": len(ordered), "study_id": study["id"],
    })
    rows = []
    for index, series in enumerate(ordered):
        start, count = series.get("start"), series.get("count")
        images = study.get("images", [])[start:start + count] if isinstance(start, int) and isinstance(count, int) else []
        display = series.get("displayNumber")
        expected_first = f"SE {display} · {_short_date(series.get('date', ''))}" if series.get("date") else ""
        areas = unique(image.get("area") for image in images if not is_transit(image))
        expected_second = "Scout" if display == 0 else (areas[0] if len(areas) == 1 else "Location unconfirmed")
        button = buttons.nth(index)
        first = button.locator(".oz-se-cap b")
        second = button.locator(".oz-se-cap > span")
        actual_first = first.inner_text().strip() if first.count() else ""
        actual_second = second.inner_text().strip() if second.count() else ""
        button_index = button.get_attribute("data-se")
        metrics = button.evaluate("""b => {
          const br=b.getBoundingClientRect(), im=b.querySelector('img')?.getBoundingClientRect();
          const cap=b.querySelector('.oz-se-cap'), first=cap?.querySelector('b'), second=cap?.querySelector('span');
          const box=e=>{if(!e)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,right:r.right,width:r.width,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,overflow:s.overflow,textOverflow:s.textOverflow}};
          return {button:box(b),thumb:box(b.querySelector('img')),first:box(first),second:box(second)};
        }""")
        evidence.check(f"strip.labels.{width}.{index}",
                       button_index == str(index) and actual_first == expected_first and actual_second == expected_second,
                       {"button_index": button_index, "expected_button_index": str(index), "displayNumber": display, "actual_first": actual_first, "expected_first": expected_first,
                        "actual_second": actual_second, "expected_second": expected_second,
                        "series_areas": areas, "source_places": unique(image.get("place") for image in images)})
        evidence.check(f"strip.cell-equals-thumbnail.{width}.{index}",
                       bool(metrics.get("button") and metrics.get("thumb") and abs(metrics["button"]["width"] - metrics["thumb"]["width"]) <= 0.75),
                       metrics)
        evidence.check(f"strip.text-does-not-widen-cell.{width}.{index}",
                       bool(metrics.get("button") and metrics.get("first") and metrics.get("second")
                            and metrics["first"]["width"] <= metrics["button"]["width"] + 0.75
                            and metrics["second"]["width"] <= metrics["button"]["width"] + 0.75),
                       metrics)
        evidence.check(f"strip.date-fits-and-area-ellipsis-is-bounded.{width}.{index}",
                       bool(metrics.get("button") and metrics.get("first") and metrics.get("second")
                            and metrics["first"]["scrollWidth"] <= metrics["first"]["clientWidth"] + 0.75
                            and metrics["second"]["overflow"] != "visible"
                            and metrics["second"]["textOverflow"] == "ellipsis"
                            and metrics["second"]["clientWidth"] <= metrics["button"]["width"] + 0.75),
                       metrics)
        evidence.check(f"strip.one-area-per-ordinary-series.{width}.{index}",
                       display == 0 or len(areas) == 1,
                       {"displayNumber": display, "ordinary_areas": areas, "source_places": unique(image.get("place") for image in images)})
        rows.append(metrics)
    gaps = [rows[index]["button"]["x"] - rows[index - 1]["button"]["right"] for index in range(1, len(rows))]
    strip_gap = page.locator("[data-series]").evaluate("el => parseFloat(getComputedStyle(el).columnGap || getComputedStyle(el).gap) || 0")
    gap_ok = all(abs(gap - strip_gap) <= 0.75 for gap in gaps) and (not gaps or max(gaps) - min(gaps) <= 0.75)
    evidence.check(f"strip.equal-gap-across-entire-study.{width}", gap_ok, {"actual_gaps": gaps, "computed_gap": strip_gap})


def test_real_payload_areas_worklist_and_australia_strip_geometry():
    evidence = AcceptanceEvidence()
    source = json.loads(DATA_PATH.read_text())
    focus = _focus_studies(source)
    missing = [key for key, study in focus.items() if study is None]
    evidence.check("source.six-required-studies-present", not missing, {"missing": missing})
    evidence.report["focus_study_ids"] = {key: study.get("id") if study else None for key, study in focus.items()}
    evidence.report["source_image_count"] = sum(len(study.get("images", [])) for study in source.get("studies", []))
    missing_area = []
    missing_order = []
    mapping_errors = []
    area_order_errors = []
    expected_worklist_lines = {}
    for key, study in focus.items():
        if not study:
            continue
        order = study.get("areaOrder")
        ordinary_areas = unique(image.get("area") for image in study.get("images", []) if not is_transit(image))
        if not isinstance(order, list) or not order or any(not isinstance(value, str) or not value.strip() for value in order) or len(order) != len(set(order)):
            missing_order.append({"study": study.get("id"), "areaOrder": order})
        elif set(order) != set(study.get("areaMap", {}).values()):
            area_order_errors.append({"study": study.get("id"), "areaOrder": order, "ordinary_areas": ordinary_areas})
        for index, image in enumerate(study.get("images", [])):
            area = image.get("area")
            if not isinstance(area, str) or not area.strip():
                missing_area.append({"study": study.get("id"), "index": index, "src": image.get("src")})
            expected = _expected_area(key, image)
            if area != expected:
                mapping_errors.append({"study": study.get("id"), "index": index, "src": image.get("src"),
                                       "place": image.get("place"), "actual_area": area, "expected_area": expected})
        expected_order = _expected_area_order(key, study)
        if order != expected_order:
            area_order_errors.append({"study": study.get("id"), "areaOrder": order, "expected_explicit_areaOrder": expected_order})
        expected_worklist_lines[key] = _worklist_area_line(study)
    evidence.check("source.target-images-have-explicit-area", not missing_area, missing_area)
    evidence.check("source.target-area-is-place-map-not-inference", not mapping_errors, mapping_errors)
    evidence.check("source.areaOrder-is-explicit-complete-and-owner-ordered", not missing_order and not area_order_errors,
                   {"missing_or_invalid": missing_order, "order_mismatches": area_order_errors,
                    "note": "areaOrder is compared to the owner-specified order, never derived from image timestamps or first-visit order."})
    evidence.report["expected_worklist_area_lines"] = expected_worklist_lines
    evidence.write()

    playwright = sync_playwright().start()
    browser = None
    try:
        browser = getattr(playwright, BROWSER_NAME).launch(headless=True)
        evidence.report["browser_version"] = browser.version
        for width, height in VIEWPORTS:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", device_scale_factor=1)
            page = context.new_page()
            page.on("pageerror", lambda error: evidence.report["page_errors"].append(str(error)))
            try:
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function("document.body.classList.contains('is-ready')", timeout=20000)
                page.wait_for_function("document.querySelector('#oz-data')?.textContent?.length > 0", timeout=15000)
                page.evaluate("document.fonts.ready")
                runtime = json.loads(page.locator("#oz-data").text_content() or "{}")
                _check_real_payload(source, runtime, evidence)
                runtime_studies = {study.get("id"): study for study in runtime.get("studies", [])}
                for key, study in focus.items():
                    if not study:
                        continue
                    row = page.locator(f'.oz-row[href="#{study["id"]}"]')
                    visible = row.count() == 1 and row.is_visible()
                    evidence.check(f"worklist.row-visible.{width}.{key}", visible, {"study_id": study["id"], "count": row.count()})
                    if not visible:
                        continue
                    region = row.locator(".oz-region")
                    actual_line = region.inner_text().strip()
                    expected_line = expected_worklist_lines[key]
                    clamp_metrics = _unclamped_measurement(page, row)
                    max_two_lines = clamp_metrics["twoLineLimit"] + 1.0
                    evidence.check(f"worklist.area-order-and-transit-line.{width}.{key}", actual_line == expected_line,
                                   {"actual": actual_line, "expected": expected_line, "areaOrder": study.get("areaOrder")})
                    evidence.check(f"worklist.two-line-clamp-safety.{width}.{key}",
                                   clamp_metrics["lineClamp"] == "2" and clamp_metrics["visibleHeight"] <= max_two_lines,
                                   clamp_metrics)
                    evidence.check(f"worklist.unclamped-area-fits-two-lines.{width}.{key}",
                                   clamp_metrics["naturalHeight"] <= max_two_lines and clamp_metrics["naturalScrollHeight"] <= max_two_lines,
                                   clamp_metrics)
                    evidence.check(f"worklist.unclamped-area-wraps-within-width.{width}.{key}",
                                   clamp_metrics["naturalScrollWidth"] <= clamp_metrics["naturalClientWidth"] + 1.0,
                                   clamp_metrics)
                    evidence.check(f"worklist.area-not-hidden-by-clamp.{width}.{key}",
                                   clamp_metrics["naturalHeight"] <= clamp_metrics["visibleHeight"] + 1.0,
                                   clamp_metrics)
                    evidence.check(f"worklist.clamp-restored-after-measurement.{width}.{key}",
                                   row.locator(".oz-region").evaluate("el => getComputedStyle(el).webkitLineClamp") == "2"
                                   and row.locator("[data-acceptance-unclamped-clone]").count() == 0,
                                   {"lineClamp": row.locator(".oz-region").evaluate("el => getComputedStyle(el).webkitLineClamp"),
                                    "remaining_clones": row.locator("[data-acceptance-unclamped-clone]").count()})
                    evidence.check(f"worklist.title-remains-study-place.{width}.{key}",
                                   row.locator(".oz-place").inner_text().strip() == study.get("place"),
                                   {"actual": row.locator(".oz-place").inner_text().strip(), "expected": study.get("place")})
                    image = row.locator(".oz-thumb img")
                    row.scroll_into_view_if_needed()
                    if image.count():
                        page.wait_for_function("""selector => { const im=document.querySelector(selector); return !!im && im.complete && im.naturalWidth>0; }""",
                                               arg=f'.oz-row[href="#{study["id"]}"] .oz-thumb img', timeout=15000)
                        image.evaluate("im => im.decode()")
                evidence.check(f"worklist.no-document-horizontal-overflow.{width}",
                               page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"),
                               {"documentWidth": page.evaluate("document.documentElement.scrollWidth"), "viewportWidth": width})
                page.evaluate("scrollTo(0, 0)")
                evidence.screenshot(page, f"{width}/area-worklist.png")
            finally:
                context.close()

        australia = focus.get("australia")
        if australia:
            for width in STRIP_VIEWPORT_WIDTHS:
                height = dict(VIEWPORTS)[width]
                context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", device_scale_factor=1)
                page = context.new_page()
                page.on("pageerror", lambda error: evidence.report["page_errors"].append(str(error)))
                try:
                    page.goto(f"{BASE_URL}#{australia['id']}", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_function("document.body.classList.contains('is-ready')", timeout=20000)
                    page.wait_for_function("document.querySelector('[data-series] [data-se]')", timeout=10000)
                    page.wait_for_function("""() => { const im=document.querySelector('[data-cells] img'); return !!im && im.dataset.want && im.complete && im.naturalWidth>0; }""", timeout=15000)
                    page.locator("[data-cells] img").first.evaluate("im => im.decode()")
                    _check_strip(page, australia, evidence, width)
                    evidence.screenshot(page, f"{width}/australia-series-strip.png")
                finally:
                    context.close()
        else:
            evidence.check("strip.australia-study-present", False, {"error": "Australia source missing"})
    finally:
        if browser is not None:
            browser.close()
        playwright.stop()

    evidence.check("browser.no-page-errors", not evidence.report["page_errors"], evidence.report["page_errors"])
    evidence.finish()
