"""Real-payload browser acceptance for the Outside Studies area/series release.

This test never rewrites the page payload or intercepts application data. It reads
source data for an independent oracle and exercises the compiled/served page as-is.
Image overlays remain place-based; worklist and series grouping are area-based.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"
BASELINE_REV = "f89fb3b64bc10028a7b83b39919290bf386e7264"
BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
BROWSER_NAME = os.environ.get("OUTSIDE_BROWSER", "chromium").lower()
EVIDENCE = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR") or tempfile.mkdtemp(prefix="outside-place-acceptance-"))
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# These sequences are acceptance expectations from the owner requirements, not
# image fixtures: every value is checked against the real served payload.
TARGET_PREFIXES = {
    "pakistan": "pakistan-2026-summer",
    "australia": "australia-2026-july",
    "galapagos": "galapagos-2026-january",
    "southwest": "american-southwest-2025-october-gallery",
    "montreal": "montreal-november-2025",
    "new_zealand": "new-zealand-2026-july",
}
EXPECTED_ORDINARY_AREAS = {
    "pakistan": ["Karachi", "Islamabad", "Murree", "Lahore"],
    "australia": ["South West", "Rottnest Island", "Perth"],
    "galapagos": ["Santa Cruz", "Isabela", "San Cristóbal"],
    "southwest": ["Joshua Tree", "Grand Canyon", "Zion", "Hoover Dam"],
    "montreal": ["Montréal"],
    "new_zealand": ["Auckland", "Rotorua"],
}
EXPECTED_TRANSIT_AREAS = {
    "pakistan": ["Rome", "Tirana"],
    "australia": ["Bangkok"],
}
EXPECTED_TRANSIT_IMAGE_PLACES = {
    "pakistan": ["Rome", "Tirana"],
    "australia": ["Bangkok"],
}
EXPECTED_AREA_ORDER = {
    "pakistan": ["Rome", "Tirana", "Karachi", "Islamabad", "Murree", "Lahore"],
    "australia": ["Bangkok", "South West", "Rottnest Island", "Perth"],
    "galapagos": ["Santa Cruz", "Isabela", "San Cristóbal"],
    "southwest": ["Joshua Tree", "Las Vegas", "Grand Canyon", "Zion", "Hoover Dam"],
    "montreal": ["Montréal"],
    "new_zealand": ["Auckland", "Rotorua"],
}
USER_LISTED_AREAS = {
    "pakistan": ["Karachi", "Islamabad", "Murree", "Lahore"],
    "australia": ["South West", "Rottnest Island", "Perth"],
    "new_zealand": ["Auckland", "Rotorua"],
}
EXPECTED_AREA_BY_PLACE = {
    "pakistan": {"Nathia Gali": "Murree", "Albania": "Tirana"},
    "australia": {
        "Busselton": "South West", "Dunsborough": "South West", "Yallingup": "South West",
        "Margaret River": "South West", "Augusta": "South West", "Hamelin Bay": "South West",
        "Fremantle": "Perth",
    },
    "new_zealand": {"Waiotapu": "Rotorua"},
}
BASELINE_HIDDEN_STUDY_IDS = {
    "puerto-rico-2025-june-photos",
    "puerto-rico-2025-october",
    "georgia-2025-october",
}


def compact_date(start: str | None, end: str | None = None) -> str:
    if not start:
        return end or ""
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(end) if end else first
    except (TypeError, ValueError):
        return start if not end or end == start else f"{start} – {end}"

    def short(value: date) -> str:
        return f"{MONTHS[value.month - 1]} {value.day}"

    if first == last:
        return f"{short(first)}, {first.year}"
    if first.year == last.year and first.month == last.month:
        return f"{MONTHS[first.month - 1]} {first.day}–{last.day}, {first.year}"
    if first.year == last.year:
        return f"{short(first)} – {short(last)}, {first.year}"
    return f"{short(first)}, {first.year} – {short(last)}, {last.year}"


def compact_strip_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    return f"{MONTHS[parsed.month - 1]} {parsed.day}"


def unique(values):
    return list(dict.fromkeys(value for value in values if isinstance(value, str) and value.strip()))


def transit(image: dict) -> bool:
    return image.get("transit") is True or image.get("se") == 0


def first_se_index(study: dict, number: int) -> int | None:
    return next((i for i, image in enumerate(study.get("images", [])) if image.get("se") == number), None)


def ordinary_areas(study: dict) -> list[str]:
    present = {image.get("area") for image in study.get("images", []) if not transit(image)}
    return [area for area in study.get("areaOrder", []) if area in present]


def transit_areas(study: dict) -> list[str]:
    return unique(image.get("area") for image in study.get("images", []) if transit(image))


def location_line(study: dict) -> str:
    areas = ordinary_areas(study)
    travels = transit_areas(study)
    if len(areas) == 1 and areas[0] == study.get("place") and study.get("country"):
        areas = [study["country"]]
    text = " · ".join(areas) if areas else "Location unconfirmed"
    if travels:
        text += " · via " + ", ".join(travels)
    return text


def expected_cover(study: dict) -> dict | None:
    images = study.get("images", [])
    key = study.get("key")
    if isinstance(key, int) and not isinstance(key, bool) and 0 <= key < len(images) and not transit(images[key]):
        return images[key]
    return next((image for image in images if not transit(image)), None)


def focus_studies(data: dict) -> dict[str, dict | None]:
    result = {}
    for key, prefix in TARGET_PREFIXES.items():
        result[key] = next((study for study in data.get("studies", []) if study.get("id", "").startswith(prefix)), None)
    return result


def temporal_key(image: dict) -> str:
    return f"{image.get('d') or ''}T{image.get('t') or ''}"


def utc_temporal_key(image: dict):
    if not image.get("d") or not image.get("t"):
        return None
    try:
        local = datetime.fromisoformat(f"{image['d']}T{image['t']}")
    except (TypeError, ValueError):
        return None
    zone = str(image.get("tz") or "").strip().upper()
    if zone in ("UTC", "GMT", "Z"):
        offset = timedelta(0)
    else:
        match = re.fullmatch(r"(?:UTC|GMT)\s*([+-])(\d{1,2})(?::?(\d{2}))?", zone)
        if not match:
            return None
        hours, minutes = int(match.group(2)), int(match.group(3) or "0")
        if hours > 14 or minutes > 59:
            return None
        offset = timedelta(hours=hours, minutes=minutes)
        if match.group(1) == "-":
            offset = -offset
    return local.replace(tzinfo=timezone(offset)).astimezone(timezone.utc)


def source_semantic_issues(data: dict) -> dict:
    issues = []
    study_ids = [study.get("id") for study in data.get("studies", [])]
    if len(study_ids) != len(set(study_ids)):
        issues.append({"kind": "duplicate-study-id"})
    for study in data.get("studies", []):
        sid = study.get("id", "<missing-id>")
        images = study.get("images", [])
        series = sorted(study.get("series", []), key=lambda row: row.get("start", -1))
        if not images:
            issues.append({"study": sid, "kind": "no-images"})
        for index, image in enumerate(images):
            if not isinstance(image.get("src"), str) or not image["src"].strip():
                issues.append({"study": sid, "image_index": index, "kind": "missing-source-id"})
            gps_fields = sorted(set(image) & {"lat", "lon", "latitude", "longitude", "gps", "gpsCoordinates", "gpsPosition", "coordinates"})
            if gps_fields:
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "fields": gps_fields, "kind": "private-gps-provenance-in-public-data"})
            if not isinstance(image.get("place"), str) or not image["place"].strip():
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "kind": "missing-image-place"})
            if not isinstance(image.get("area"), str) or not image["area"].strip():
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "kind": "missing-image-area"})
            if type(image.get("transit")) is not bool:
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "kind": "transit-not-boolean"})
            if not isinstance(image.get("se"), int) or isinstance(image.get("se"), bool):
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "kind": "missing-series-display-number"})
            elif type(image.get("transit")) is bool and image["transit"] != (image["se"] == 0):
                issues.append({"study": sid, "image_index": index, "src": image.get("src"), "transit": image.get("transit"), "se": image.get("se"), "kind": "transit-flag-series-disagreement"})
        area_order = study.get("areaOrder")
        ordinary_image_areas = unique(image.get("area") for image in images if not transit(image))
        if not isinstance(area_order, list) or any(not isinstance(area, str) or not area.strip() for area in area_order):
            issues.append({"study": sid, "areaOrder": area_order, "kind": "missing-explicit-area-order"})
        elif len(area_order) != len(set(area_order)) or set(area_order) != set(study.get("areaMap", {}).values()):
            issues.append({"study": sid, "areaOrder": area_order, "ordinary_areas": ordinary_image_areas, "kind": "area-order-coverage-or-duplicate-error"})
        expected_start = 0
        displays = []
        transit_rows = []
        for row in series:
            start, count, display = row.get("start"), row.get("count"), row.get("displayNumber")
            if not isinstance(start, int) or isinstance(start, bool) or not isinstance(count, int) or isinstance(count, bool):
                issues.append({"study": sid, "series": row, "kind": "invalid-series-range"})
                continue
            if start != expected_start or count < 1:
                issues.append({"study": sid, "series": row, "expected_start": expected_start, "kind": "series-range-gap-or-overlap"})
            expected_start = start + count
            if not isinstance(display, int) or isinstance(display, bool):
                issues.append({"study": sid, "series": row, "kind": "missing-series-display-number"})
            else:
                displays.append(display)
            chunk = images[max(0, start):max(0, start) + max(0, count)]
            flags = [transit(image) for image in chunk]
            if any(flags):
                transit_rows.append(row)
                if display != 0 or not all(flags):
                    issues.append({"study": sid, "series": row, "kind": "transit-not-one-scout-series"})
            elif display == 0:
                issues.append({"study": sid, "series": row, "kind": "ordinary-image-in-se0"})
            for image in chunk:
                if display != image.get("se"):
                    issues.append({"study": sid, "src": image.get("src"), "series_display": display, "image_se": image.get("se"), "kind": "image-series-mismatch"})
            areas = unique(image.get("area") for image in chunk)
            ordinary = [image for image in chunk if not transit(image)]
            if ordinary and len(areas) > 1:
                issues.append({"study": sid, "series": row, "areas": areas, "kind": "area-not-uniform-in-ordinary-series"})
            dates = unique(image.get("d") for image in ordinary)
            if len(dates) > 1:
                issues.append({"study": sid, "series": row, "dates": dates, "kind": "date-not-uniform-in-ordinary-series"})
            if ordinary and all(image.get("d") for image in ordinary):
                series_date = row.get("date")
                if series_date and series_date not in dates:
                    issues.append({"study": sid, "series": row, "dates": dates, "kind": "series-date-not-image-date"})
        if expected_start != len(images):
            issues.append({"study": sid, "covered_images": expected_start, "image_count": len(images), "kind": "series-count-does-not-cover-images"})
        all_transit = [image for image in images if transit(image)]
        if all_transit and len(transit_rows) != 1:
            issues.append({"study": sid, "transit_series_count": len(transit_rows), "kind": "transit-not-single-se0"})
        if len(all_transit) > 1:
            utc_keys = [utc_temporal_key(image) for image in all_transit]
            if all(key is not None for key in utc_keys):
                known_utc_keys = [key for key in utc_keys if key is not None]
                if known_utc_keys != sorted(known_utc_keys):
                    issues.append({"study": sid, "sources": [image.get("src") for image in all_transit], "kind": "scout-not-time-ordered"})
            elif all(image.get("d") and image.get("t") for image in all_transit) and len(unique(image.get("tz") for image in all_transit)) == 1:
                local_keys = [temporal_key(image) for image in all_transit]
                if local_keys != sorted(local_keys):
                    issues.append({"study": sid, "sources": [image.get("src") for image in all_transit], "kind": "scout-not-time-ordered"})
            else:
                issues.append({"study": sid, "sources": [image.get("src") for image in all_transit], "kind": "scout-time-order-unverified"})
        if not all_transit and transit_rows:
            issues.append({"study": sid, "kind": "unexpected-scout-series"})
        wanted_numbers = list(range(0 if all_transit else 1, (0 if all_transit else 1) + len(series)))
        if displays != wanted_numbers:
            issues.append({"study": sid, "observed": displays, "expected": wanted_numbers, "kind": "nonconsecutive-series-display-numbers"})
        # Each consecutive ordinary DATE+AREA run is one series; no source
        # reordering or timestamp-derived area ordering is permitted.
        ordinary = [(i, image) for i, image in enumerate(images) if not transit(image)]
        for (previous_index, previous), (current_index, current) in zip(ordinary, ordinary[1:]):
            changed = previous.get("d") != current.get("d") or previous.get("area") != current.get("area")
            if changed and previous.get("se") == current.get("se"):
                issues.append({"study": sid, "srcs": [previous.get("src"), current.get("src")], "kind": "missing-series-boundary-on-date-or-area-change"})
            if not changed and previous.get("se") != current.get("se"):
                issues.append({"study": sid, "srcs": [previous.get("src"), current.get("src")], "kind": "nonmaximal-date-area-series-boundary"})
        if ordinary and all(image.get("d") for _, image in ordinary):
            dates = [image.get("d") for _, image in ordinary]
            expected_span = (min(dates), max(dates))
            if (study.get("date"), study.get("dateEnd") or study.get("date")) != expected_span:
                issues.append({"study": sid, "expected_nontransit_span": expected_span,
                               "study_span": (study.get("date"), study.get("dateEnd")),
                               "kind": "study-date-range-not-derived-from-nontransit-images"})
    return {"issue_count": len(issues), "issues": issues}


def make_study_table(data: dict) -> list[dict]:
    rows = []
    for study in data.get("studies", []):
        images = study.get("images", [])
        series_rows = []
        for series in sorted(study.get("series", []), key=lambda item: item.get("displayNumber", -1)):
            start, count = series.get("start", 0), series.get("count", 0)
            chunk = images[start:start + count] if isinstance(start, int) and isinstance(count, int) else []
            series_rows.append({
                "se": series.get("displayNumber"), "title": series.get("title"),
                "date": series.get("date"), "dateEnd": series.get("dateEnd"),
                "image_count": count, "areas": unique(image.get("area") for image in chunk),
                "places": unique(image.get("place") for image in chunk),
                "transit_areas": unique(image.get("area") for image in chunk if transit(image)),
                "transit_places": unique(image.get("place") for image in chunk if transit(image)),
                "source_ids": [image.get("src") for image in chunk],
            })
        rows.append({
            "study_id": study.get("id"), "title": study.get("place"),
            "date": study.get("date"), "dateEnd": study.get("dateEnd"),
            "image_count": len(images), "status": study.get("status"),
            "area_order": study.get("areaOrder"),
            "ordinary_areas": ordinary_areas(study), "transit_areas": transit_areas(study),
            "ordinary_places": unique(image.get("place") for image in images if not transit(image)),
            "transit_places": unique(image.get("place") for image in images if transit(image)),
            "series": series_rows,
        })
    return rows


class Evidence:
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.report = {
            "schema": "outside-area-series-real-acceptance-v1",
            "status": "INCOMPLETE",
            "phase": os.environ.get("OUTSIDE_PHASE", "candidate"),
            "candidate_url": BASE_URL,
            "browser": BROWSER_NAME,
            "viewport_requirements": [{"width": 375, "height": 812}, {"width": 1440, "height": 1000}],
            "additional_viewport": {"width": 1024, "height": 900},
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "source_path": str(DATA_PATH), "baseline_revision": BASELINE_REV,
            "checks": [], "screenshots": [], "page_errors": [], "unlisted_area_review": [],
        }
        self.failures = []
        self.write()

    def write(self):
        self.report["updated_utc"] = datetime.now(timezone.utc).isoformat()
        temp = self.path / "acceptance-receipt.json.tmp"
        temp.write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + "\n")
        temp.replace(self.path / "acceptance-receipt.json")

    def check(self, check_id: str, passed: bool, details=None):
        row = {"id": check_id, "status": "PASS" if passed else "FAIL", "details": details}
        self.report["checks"].append(row)
        if not passed:
            self.failures.append({"id": check_id, "details": details})
        self.write()
        return passed

    def failed_exception(self, check_id: str, exc: Exception):
        self.check(check_id, False, {"error": repr(exc), "traceback": traceback.format_exc()})

    def screenshot(self, page, name: str, locator=None, full_page=False):
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            if locator is None:
                page.screenshot(path=str(target), full_page=full_page, animations="disabled")
            else:
                locator.screenshot(path=str(target), animations="disabled")
            from PIL import Image
            with Image.open(target) as image:
                rgb = image.convert("RGB")
                sample = rgb.resize((min(48, rgb.width), min(48, rgb.height)))
                colors = len(set(sample.getdata()))
                size = list(rgb.size)
            record = {"path": str(target), "bytes": target.stat().st_size, "pixels": size, "sample_unique_colors": colors}
            self.report["screenshots"].append(record)
            self.check(f"screenshot.{name}", record["bytes"] > 1000 and colors > 8, record)
            return str(target)
        except Exception as exc:
            self.failed_exception(f"screenshot.{name}", exc)
            return None


def _same_json(left, right) -> bool:
    return json.dumps(left, ensure_ascii=False, sort_keys=True, separators=(",", ":")) == json.dumps(right, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _row_box(page, selector: str) -> dict:
    return page.locator(selector).evaluate("""el => {
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      return {x:r.x, y:r.y, width:r.width, height:r.height, right:r.right,
        scrollWidth:el.scrollWidth, clientWidth:el.clientWidth,
        whiteSpace:cs.whiteSpace, lineClamp:cs.webkitLineClamp,
        lineHeight:parseFloat(cs.lineHeight) || 0, flexShrink:cs.flexShrink,
        textOverflow:cs.textOverflow};
    }""")


def _worklist_row_checks(page, study: dict, evidence: Evidence, width: int):
    sid = study["id"]
    row = page.locator(f'.oz-row[href="#{sid}"]')
    exists = row.count() == 1 and row.is_visible()
    evidence.check(f"worklist.row-visible.{width}.{sid}", exists, {"study_id": sid, "count": row.count()})
    if not exists:
        return
    title = row.locator(".oz-rowtext > .oz-place").inner_text().strip()
    date_text = row.locator(".oz-rowtext > .oz-row-dates > .oz-row-date").inner_text().strip()
    count_text = row.locator(".oz-rowtext > .oz-row-dates > .oz-row-count").inner_text().strip()
    area_line = row.locator(".oz-rowtext > .oz-region").inner_text().strip()
    area_metrics = _row_box(page, f'.oz-row[href="#{sid}"] .oz-region')
    row_metrics = _row_box(page, f'.oz-row[href="#{sid}"]')
    date_box = row.locator(".oz-row-date").bounding_box()
    count_box = row.locator(".oz-row-count").bounding_box()
    status_box = row.locator(".oz-status").bounding_box()
    date_metrics = _row_box(page, f'.oz-row[href="#{sid}"] .oz-row-date')
    count_metrics = _row_box(page, f'.oz-row[href="#{sid}"] .oz-row-count')
    boxes_disjoint = bool(date_box and count_box and (
        date_box["x"] + date_box["width"] <= count_box["x"] + 1
        or count_box["x"] + count_box["width"] <= date_box["x"] + 1
        or date_box["y"] + date_box["height"] <= count_box["y"] + 1
        or count_box["y"] + count_box["height"] <= date_box["y"] + 1
    ))
    count_positioned_below_badge = bool(count_box and status_box and count_box["y"] >= status_box["y"] + status_box["height"] - 1)
    count_protected = count_metrics["flexShrink"] == "0" or count_positioned_below_badge
    expected_date = compact_date(study.get("date", ""), study.get("dateEnd", ""))
    evidence.check(f"worklist.title.{width}.{sid}", title == study.get("place"), {"actual": title, "expected": study.get("place")})
    evidence.check(f"worklist.date-and-count.{width}.{sid}", date_text == expected_date and count_text == f"{len(study['images'])} IM" and boxes_disjoint and date_metrics["scrollWidth"] <= date_metrics["clientWidth"] and count_protected and count_metrics["whiteSpace"] == "nowrap" and count_metrics["scrollWidth"] <= count_metrics["clientWidth"],
                   {"date": date_text, "expected_date": expected_date, "count": count_text, "expected_count": f"{len(study['images'])} IM", "date_and_count_boxes_disjoint": boxes_disjoint,
                    "date_metrics": date_metrics, "count_metrics": count_metrics, "count_below_badge": count_positioned_below_badge})
    expected_area_line = location_line(study)
    evidence.check(f"worklist.area-order-line.{width}.{sid}", area_line == expected_area_line,
                   {"actual": area_line, "expected": expected_area_line, "areaOrder": study.get("areaOrder")})
    evidence.check(f"worklist.no-horizontal-overflow.{width}.{sid}", row_metrics["scrollWidth"] <= row_metrics["clientWidth"] and area_metrics["scrollWidth"] <= area_metrics["clientWidth"],
                   {"row": row_metrics, "area_line": area_metrics})
    evidence.check(f"worklist.area-two-lines.{width}.{sid}", area_metrics["whiteSpace"] == "normal" and area_metrics["lineClamp"] == "2" and area_metrics["height"] <= area_metrics["lineHeight"] * 2 + 2,
                   area_metrics)
    repeated_title = bool(title and title.casefold() in area_line.casefold())
    evidence.check(f"worklist.no-title-in-area-line.{width}.{sid}", not repeated_title, {"title": title, "area_line": area_line})
    if sid.startswith("montreal-august-2023") or sid.startswith("montreal-november-2025"):
        evidence.check(f"worklist.montreal-country.{width}.{sid}", area_line.startswith("Canada"), {"area_line": area_line})
    image = expected_cover(study)
    thumb = row.locator(".oz-thumb img").get_attribute("src") or ""
    expected_thumb = f"{image['src']}-s.webp" if image else ""
    thumb_path = thumb.split("?", 1)[0]
    evidence.check(f"worklist.nontransit-thumbnail.{width}.{sid}", not image or (thumb_path.endswith(expected_thumb) and not transit(image)),
                   {"thumbnail": thumb, "expected_source": expected_thumb, "cover_is_transit": bool(image and transit(image))})


def _capture_row(page, row, key: str, evidence: Evidence, width: int):
    try:
        row.scroll_into_view_if_needed()
        image = row.locator(".oz-thumb img")
        if image.count():
            selector = f'.oz-row[href="{row.get_attribute("href")}"] .oz-thumb img'
            page.wait_for_function(r"""selector => {
              const img=document.querySelector(selector);
              if(!img || !img.complete || img.naturalWidth<=0 || !img.currentSrc) return false;
              return new URL(img.currentSrc).pathname.replace(/-(s|m|l)\.webp$/, '') === new URL(img.getAttribute('src'),location.href).pathname.replace(/-(s|m|l)\.webp$/, '');
            }""", arg=selector, timeout=12000)
        evidence.screenshot(page, f"{width}/row-{key}.png", locator=row)
    except Exception as exc:
        evidence.failed_exception(f"screenshot.row-{width}-{key}", exc)


def _wait_image(page, expected_src: str, timeout=15000):
    page.wait_for_function("""expected => {
      const img = document.querySelector('[data-cells] img');
      if (!img || img.dataset.want !== expected) return false;
      if (!img.complete || img.naturalWidth <= 0 || !img.currentSrc) return false;
      try { return new URL(img.currentSrc).href === new URL(img.dataset.want, location.href).href; }
      catch { return false; }
    }""", arg=expected_src, timeout=timeout)
    page.locator("[data-cells] img").first.evaluate("img => img.decode()")


def _active_source(page) -> str:
    value = page.locator("[data-cells] img").first.get_attribute("data-want") or ""
    return re.sub(r"-(?:s|m|l)\.webp(?:\?.*)?$", "", value)


def _source_base(image: dict) -> str:
    return image.get("src", "")


def _overlay_metrics(page) -> dict:
    return page.evaluate("""() => {
      const names=['tl','tr','bl','br']; const boxes={}; const lines={};
      for (const name of names) {
        const el=document.querySelector(`[data-ov=${name}]`), r=el.getBoundingClientRect();
        boxes[name]={left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
        lines[name]=[...el.children].map(n=>{const cs=getComputedStyle(n),b=n.getBoundingClientRect();
          return {text:n.textContent.trim(),whiteSpace:cs.whiteSpace,overflowX:cs.overflowX,textOverflow:cs.textOverflow,lineHeight:parseFloat(cs.lineHeight),scrollWidth:n.scrollWidth,clientWidth:n.clientWidth,
            left:b.left,right:b.right,top:b.top,bottom:b.bottom};});
      }
      const overlap=[];
      for(let i=0;i<names.length;i++)for(let j=i+1;j<names.length;j++){
        const a=boxes[names[i]],b=boxes[names[j]];
        if(Math.min(a.right,b.right)>Math.max(a.left,b.left)+0.5 && Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+0.5)
          overlap.push([names[i],names[j]]);
      }
      return {boxes,lines,overlap,viewport:{width:innerWidth,height:innerHeight}};
    }""")


def _check_overlay(page, study: dict, image: dict, evidence: Evidence, key: str, width: int, label: str):
    tl = page.locator('[data-ov="tl"]').locator(":scope > div").all_inner_texts()
    expected_image = image.get("place", "").upper() + (" · TRANSIT" if transit(image) else "")
    start, end = study.get("date", ""), study.get("dateEnd", "")
    expected_date = start if not end or start == end else f"{start} to {end[5:] if start[:4] == end[:4] else end}"
    xc = tl[3] if len(tl) > 3 else ""
    evidence.check(f"overlay.title-place-date-xc.{width}.{key}.{label}",
                   len(tl) == 4 and tl[0] == study.get("place", "").upper() and tl[1] == expected_image and tl[2] == f"STUDY {expected_date}" and xc.startswith("XC · "),
                   {"lines": tl, "expected_image_line": expected_image, "expected_study_date": expected_date})
    metrics = _overlay_metrics(page)
    all_lines = [line for rows in metrics["lines"].values() for line in rows]
    line_valid = all(line["whiteSpace"] in ("nowrap", "pre") and line["bottom"] - line["top"] <= line["lineHeight"] + 1 and (line["scrollWidth"] <= line["clientWidth"] or (line["overflowX"] == "hidden" and line["textOverflow"] == "ellipsis")) for line in all_lines)
    evidence.check(f"overlay.lines-no-wrap-or-overflow.{width}.{key}.{label}", line_valid, metrics["lines"])
    evidence.check(f"overlay.boxes-disjoint.{width}.{key}.{label}", not metrics["overlap"], metrics)
    return metrics


def _check_series_strip(page, study: dict, evidence: Evidence, key: str, width: int):
    for index, series in enumerate(study.get("series", [])):
        start, count = series.get("start", 0), series.get("count", 0)
        images = study.get("images", [])[start:start + count] if isinstance(start, int) and isinstance(count, int) else []
        display = series.get("displayNumber")
        is_scout = display == 0
        areas = unique(image.get("area") for image in images if not transit(image))
        expected_title = f"SE {display} · {compact_strip_date(series.get('date', ''))}"
        expected_area = "Scout" if is_scout else (areas[0] if len(areas) == 1 else "Location unconfirmed")
        button = page.locator(f'[data-series] [data-se="{index}"]')
        title = button.locator(".oz-se-cap b")
        area_label = button.locator(".oz-se-cap > span")
        actual_title = title.inner_text().strip() if title.count() else ""
        actual_area = area_label.inner_text().strip() if area_label.count() else ""
        metrics = {
            "first_line": title.evaluate("el => ({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,textOverflow:getComputedStyle(el).textOverflow})") if title.count() else {},
            "second_line": area_label.evaluate("el => ({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,textOverflow:getComputedStyle(el).textOverflow})") if area_label.count() else {},
        }
        evidence.check(f"series.strip-date-first-area-second.{width}.{key}.{display}",
                       bool(images) and actual_title == expected_title and actual_area == expected_area,
                       {"study_id": study.get("id"), "series_index": index, "display_number": display,
                        "actual_first_line": actual_title, "expected_first_line": expected_title,
                        "actual_second_line": actual_area, "expected_second_line": expected_area,
                        "series_areas": areas, "image_places": unique(image.get("place") for image in images), "metrics": metrics})


def _serve_route_cases(page, cases: list[dict]) -> dict:
    if BROWSER_NAME != "webkit":
        return _serve_route_batch(page, cases)
    # WebKit enforces 100 History API writes per ten seconds per page.
    # Fresh pages keep exhaustive route checks inside that native limit.
    result = {"checked": 0, "failures": []}
    for offset in range(0, len(cases), 60):
        route_page = page.context.new_page()
        try:
            route_page.goto(BASE_URL, wait_until="domcontentloaded")
            route_page.wait_for_function("document.body.classList.contains('is-ready')")
            batch = _serve_route_batch(route_page, cases[offset:offset + 60])
            result["checked"] += batch["checked"]
            result["failures"].extend(batch["failures"])
        finally:
            route_page.close()
    return result


def _serve_route_batch(page, cases: list[dict]) -> dict:
    if not cases:
        return {"checked": 0, "failures": []}
    return page.evaluate("""cases => {
      const failures=[];
      for (const item of cases) {
        history.replaceState(history.state, '', item.fragment);
        window.dispatchEvent(new PopStateEvent('popstate'));
        const img=document.querySelector('[data-cells] img');
        const actual=(img?.dataset.want||'').replace(/-(?:s|m|l)\\.webp(?:\\?.*)?$/,'');
        const alert=document.querySelector('[data-route-error]');
        const error=!!alert && !alert.hidden && getComputedStyle(alert).display!=='none';
        const okay=item.expected===null ? error : (!error && actual===item.expected);
        if(!okay && failures.length<40) failures.push({fragment:item.fragment,expected:item.expected,actual,error});
      }
      return {checked:cases.length,failures};
    }""", cases)


def _baseline_routes_for_focus(data: dict, focus: dict[str, dict | None]) -> tuple[list[dict], str | None]:
    try:
        raw = subprocess.check_output(["git", "show", f"{BASELINE_REV}:src/data/outside-studies.json"], cwd=ROOT, text=True, timeout=15)
        baseline = json.loads(raw)
    except Exception as exc:
        return [], f"historical route ledger unavailable: {exc!r}"
    focus_ids = {study.get("id") for study in focus.values() if study}
    routes: dict[str, str] = {}
    baseline_studies = {study.get("id"): study for study in baseline.get("studies", [])}
    prior_focus_sources = {
        image.get("src")
        for study in baseline.get("studies", []) if study.get("id") in focus_ids
        for image in study.get("images", [])
    }
    for study in baseline.get("studies", []):
        if study.get("id") not in focus_ids:
            continue
        for index, image in enumerate(study.get("images", []), 1):
            src = image.get("src")
            routes[f"#{study['id']}/{index}"] = src
    for alias_id, alias in baseline.get("aliases", {}).items():
        if isinstance(alias.get("targets"), list):
            targets = alias["targets"]
            default_target = alias.get("defaultTarget")
            if default_target is None and "defaultTarget" not in alias:
                default_target = next((target for target in targets if target), None)
            def source_for(target):
                if not isinstance(target, dict):
                    return None
                study = baseline_studies.get(target.get("studyId"))
                index = target.get("index")
                if not study or not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(study.get("images", [])):
                    return None
                return study["images"][index].get("src")
            default_src = source_for(default_target)
            if default_src in prior_focus_sources:
                routes[f"#{alias_id}"] = default_src
            for ordinal, target in enumerate(targets, 1):
                src = source_for(target)
                if src in prior_focus_sources:
                    routes[f"#{alias_id}/{ordinal}"] = src
        else:
            study = baseline_studies.get(alias.get("studyId"))
            if not study:
                continue
            indices = alias.get("indices", [])
            default_index = alias.get("defaultIndex")
            if default_index is None:
                default_index = next((index for index in indices if isinstance(index, int) and not isinstance(index, bool) and index >= 0), None)
            def source_at(index):
                return study["images"][index].get("src") if isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(study.get("images", [])) else None
            src = source_at(default_index)
            if src in prior_focus_sources:
                routes[f"#{alias_id}"] = src
            for ordinal, index in enumerate(indices, 1):
                src = source_at(index)
                if src in prior_focus_sources:
                    routes[f"#{alias_id}/{ordinal}"] = src
    current_refs_all = {image.get("src") for study in data.get("studies", []) for image in study.get("images", [])}
    cases = [{"fragment": fragment, "expected": src if src in current_refs_all else None} for fragment, src in sorted(routes.items())]
    return cases, None


def _evaluate_data_requirements(data: dict, focus: dict[str, dict | None], evidence: Evidence):
    semantic = source_semantic_issues(data)
    evidence.report["source_semantics"] = semantic
    evidence.check("data.all-image-area-place-transit-se-series-and-count-integrity", semantic["issue_count"] == 0, semantic)
    evidence.report["study_table"] = make_study_table(data)
    missing_targets = [key for key, study in focus.items() if study is None]
    evidence.check("data.required-study-groups-present", not missing_targets, {"missing_groups": missing_targets})

    date_format_cases = {
        "same-month": ("2026-07-17", "2026-07-19", "Jul 17–19, 2026"),
        "same-year": ("2026-06-28", "2026-07-05", "Jun 28 – Jul 5, 2026"),
        "cross-year": ("2025-12-30", "2026-01-02", "Dec 30, 2025 – Jan 2, 2026"),
    }
    formats = {name: {"actual": compact_date(start, end), "expected": expected} for name, (start, end, expected) in date_format_cases.items()}
    evidence.check("data.required-compact-date-formats", all(row["actual"] == row["expected"] for row in formats.values()), formats)

    unlisted_areas = []
    areas_ok = True
    for key, study in focus.items():
        if not study:
            continue
        observed = ordinary_areas(study)
        expected = EXPECTED_ORDINARY_AREAS[key]
        if key == "southwest" and "Las Vegas" in observed:
            expected = ["Joshua Tree", "Las Vegas", "Grand Canyon", "Zion", "Hoover Dam"]
        # These are explicit contract orders, not image timestamps or first-visit order.
        expected_order = EXPECTED_AREA_ORDER[key]
        area_order = study.get("areaOrder")
        sequence_ok = observed == expected and area_order == expected_order
        if key in EXPECTED_TRANSIT_AREAS:
            got_transit = transit_areas(study)
            sequence_ok = sequence_ok and got_transit == EXPECTED_TRANSIT_AREAS[key]
            overlay_transit_places = unique(image.get("place") for image in study.get("images", []) if transit(image))
            sequence_ok = sequence_ok and overlay_transit_places == EXPECTED_TRANSIT_IMAGE_PLACES[key]
            if key == "pakistan":
                sequence_ok = sequence_ok and "Albania" not in overlay_transit_places
            se1_index = first_se_index(study, 1)
            se0_index = first_se_index(study, 0)
            first_ordinary = study.get("images", [])[se1_index].get("area") if se1_index is not None else None
            first_scout = study.get("images", [])[se0_index].get("area") if se0_index is not None else None
            sequence_ok = sequence_ok and first_ordinary == expected[0] and first_scout == EXPECTED_TRANSIT_AREAS[key][0]
        if key == "southwest":
            sequence_ok = sequence_ok and bool(study.get("images")) and study["images"][-1].get("area") == "Hoover Dam"
        if key == "pakistan":
            ordinary_dates = [image.get("d") for image in study["images"] if not transit(image) and image.get("d")]
            expected_span = (min(ordinary_dates), max(ordinary_dates)) if ordinary_dates else (None, None)
            sequence_ok = sequence_ok and (study.get("date"), study.get("dateEnd")) == expected_span == ("2026-06-28", "2026-07-05")
        if key == "australia":
            ordinary_dates = [image.get("d") for image in study["images"] if not transit(image) and image.get("d")]
            expected_span = (min(ordinary_dates), max(ordinary_dates)) if ordinary_dates else (None, None)
            sequence_ok = sequence_ok and (study.get("date"), study.get("dateEnd")) == expected_span
        if key in ("galapagos", "southwest", "montreal", "new_zealand"):
            ordinary_dates = [image.get("d") for image in study["images"] if not transit(image) and image.get("d")]
            if ordinary_dates:
                sequence_ok = sequence_ok and (study.get("date"), study.get("dateEnd")) == (min(ordinary_dates), max(ordinary_dates))
        areas_ok = areas_ok and sequence_ok
        known_areas = set(expected_order) | set(EXPECTED_TRANSIT_AREAS.get(key, []))
        for image_index, image in enumerate(study.get("images", [])):
            area = image.get("area")
            place = image.get("place")
            expected_area = EXPECTED_AREA_BY_PLACE.get(key, {}).get(place, place)
            flagged = any(any(token in str(field).casefold() for token in ("guess", "unlisted", "confirm")) and bool(value)
                          for field, value in image.items())
            if area != expected_area or not area or area not in known_areas or flagged:
                unlisted_areas.append({
                    "study_id": study.get("id"), "group": key, "image_index": image_index,
                    "source_id": image.get("src"), "place": place, "area": area,
                    "expected_area_from_explicit_place_map": expected_area,
                    "date": image.get("d"), "time": image.get("t"), "se": image.get("se"),
                    "transit": transit(image),
                    "evidence": {"source_id": image.get("src"), "capture_date": image.get("d"), "capture_time": image.get("t"),
                                 "display_place_label": place, "area_label": area,
                                 "note": "Area is an explicit owner mapping; no GPS or geocoder inference is used."},
                })
    evidence.report["unlisted_area_review"] = unlisted_areas
    evidence.check("data.priority-area-order-and-nontransit-dates", areas_ok,
                   {"focus_areas": {key: {"ordinary": ordinary_areas(study), "transit": transit_areas(study),
                                          "areaOrder": study.get("areaOrder"),
                                          "date": study.get("date"), "dateEnd": study.get("dateEnd")}
                                    for key, study in focus.items() if study},
                    "required_order": EXPECTED_AREA_ORDER, "unlisted_area_review_count": len(unlisted_areas)})

    montreal = focus.get("montreal")
    evidence.check("data.montreal-country-present-for-worklist", bool(montreal and montreal.get("country") == "Canada" and location_line(montreal) == "Canada"),
                   {"study_id": montreal.get("id") if montreal else None, "country": montreal.get("country") if montreal else None,
                    "expected_worklist_area_line": "Canada", "derived_area_line": location_line(montreal) if montreal else None})
    evidence.write()


def _open_route(page, fragment: str):
    # A direct-link assertion must load a document, not reuse an already-open
    # mobile reader through same-document fragment navigation.
    page.goto("about:blank")
    page.goto(urljoin(BASE_URL, fragment), wait_until="domcontentloaded", timeout=30000)
    page.wait_for_function("document.body.classList.contains('is-ready')", timeout=20000)
    page.wait_for_function("document.querySelector('#oz-data')?.textContent?.length > 0", timeout=15000)


def _run_overlay_acceptance(page, key: str, study: dict, evidence: Evidence, width: int):
    sid = study["id"]
    se1 = first_se_index(study, 1)
    se0 = first_se_index(study, 0)
    evidence.check(f"overlay.required-se0-and-se1.{width}.{key}", se1 is not None and se0 is not None,
                   {"study_id": sid, "first_se0_index": se0, "first_se1_index": se1})
    if se1 is None or se0 is None:
        return
    ordinary = study["images"][se1]
    scout = study["images"][se0]
    _open_route(page, f"#{sid}")
    _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
    actual = _active_source(page)
    evidence.check(f"navigation.plain-hash-opens-first-se1.{width}.{key}", actual == _source_base(ordinary),
                   {"study_id": sid, "actual": actual, "expected": ordinary.get("src"), "index": se1})
    _check_overlay(page, study, ordinary, evidence, key, width, "se1")
    if width in (375, 1440):
        evidence.screenshot(page, f"{width}/overlay-{key}-se1.png")

    active_button = page.locator('[data-series] [data-se="0"]')
    cap = active_button.locator(".oz-se-cap b")
    series = next((item for item in study.get("series", []) if item.get("displayNumber") == 0), {})
    expected_label = f"SE 0 · {compact_strip_date(series.get('date', ''))}"
    expected_second_line = "Scout"
    label_text = cap.inner_text().strip() if cap.count() else ""
    label_style = cap.evaluate("el => ({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,textOverflow:getComputedStyle(el).textOverflow,whiteSpace:getComputedStyle(el).whiteSpace})") if cap.count() else {}
    scout_area = active_button.locator(".oz-se-cap > span").inner_text().strip() if active_button.count() else ""
    evidence.check(f"series.scout-date-first-scout-second.{width}.{key}",
                   label_text == expected_label and scout_area == expected_second_line and label_style.get("scrollWidth", 0) <= label_style.get("clientWidth", -1),
                   {"first_line": label_text, "expected_first_line": expected_label,
                    "second_line": scout_area, "expected_second_line": expected_second_line, "first_line_metrics": label_style})

    # PageUp from the first ordinary image must reach the first SE0 route.
    page.keyboard.press("PageUp")
    page.wait_for_function("document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '0'", timeout=8000)
    _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
    actual = _active_source(page)
    tl = page.locator('[data-ov="tl"]').locator(":scope > div").all_inner_texts()
    br = page.locator('[data-ov="br"]').inner_text().upper()
    evidence.check(f"navigation.pageup-reaches-scout.{width}.{key}", actual == _source_base(scout) and len(tl) > 1 and tl[1] == f"{scout.get('place','')} · TRANSIT".upper(),
                   {"actual": actual, "expected": scout.get("src"), "top_left": tl})
    evidence.check(f"overlay.scout-only-not-prelim.{width}.{key}", "SCOUT" in br and "PRELIM" not in br,
                   {"bottom_right": br})
    scout_badge = page.locator('[data-ov="br"] .oz-ov-status.oz-st-prelim').filter(has_text=re.compile(r"^SCOUT$"))
    evidence.check(f"overlay.scout-retains-prelim-style.{width}.{key}", scout_badge.count() == 1,
                   {"badge_count": scout_badge.count(), "class": scout_badge.get_attribute("class") if scout_badge.count() else None})
    _check_overlay(page, study, scout, evidence, key, width, "se0-pageup")
    if width in (375, 1440):
        evidence.screenshot(page, f"{width}/overlay-{key}-se0-pageup.png")

    # The visible strip is an independent route into SE0.
    active_button.click()
    _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
    evidence.check(f"navigation.scout-strip-click.{width}.{key}", _active_source(page) == _source_base(scout),
                   {"actual": _active_source(page), "expected": scout.get("src")})
    series_title = active_button.locator(".oz-se-cap b").inner_text().strip()
    evidence.check(f"series.title-not-clipped.{width}.{key}", series_title == expected_label and label_style.get("scrollWidth", 0) <= label_style.get("clientWidth", -1),
                   {"actual": series_title, "expected": expected_label, "metrics": label_style})

    # Starting on SE1, a native wheel input back toward earlier material must expose SE0.
    ordinary_button = page.locator('[data-series] [data-se="1"]')
    ordinary_button.click()
    _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
    vp = page.locator("[data-viewport]").bounding_box()
    if vp:
        page.mouse.move(vp["x"] + vp["width"] / 2, vp["y"] + vp["height"] / 2)
        page.mouse.wheel(0, -120)
        page.wait_for_function("document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '0'", timeout=8000)
        _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
        scout_sources = {im["src"] for im in study["images"] if transit(im)}
        evidence.check(f"navigation.wheel-reaches-scout.{width}.{key}", _active_source(page) in scout_sources,
                       {"actual": _active_source(page), "allowed_transit_sources": sorted(scout_sources)})
    else:
        evidence.check(f"navigation.wheel-reaches-scout.{width}.{key}", False, {"error": "viewer viewport has no box"})

    if key == "australia":
        rot_index = next((i for i, item in enumerate(study.get("series", [])) if study["images"][item["start"]].get("area") == "Rottnest Island"), None)
        rot_series = study["series"][rot_index] if rot_index is not None else None
        rot_title = f"SE {rot_series['displayNumber']} · {compact_strip_date(rot_series.get('date', ''))}" if rot_series else ""
        rot_button = page.locator(f'[data-series] [data-se="{rot_index}"]')
        rot_images = study.get("images", [])[rot_series.get("start", 0):rot_series.get("start", 0) + rot_series.get("count", 0)] if rot_series else []
        rot_cap = rot_button.locator(".oz-se-cap b")
        rot_area_label = rot_button.locator(".oz-se-cap > span")
        if rot_button.count():
            rot_button.scroll_into_view_if_needed()
        actual_name = rot_cap.inner_text().strip() if rot_cap.count() else ""
        actual_area = rot_area_label.inner_text().strip() if rot_area_label.count() else ""
        rot_metrics = rot_cap.evaluate("el => ({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,textOverflow:getComputedStyle(el).textOverflow})") if rot_cap.count() else {}
        expected_area = "Rottnest Island"
        evidence.check(f"series.rottnest-date-first-area-second.{width}", bool(rot_series and rot_images) and rot_images[0].get("area") == expected_area and actual_name == rot_title and actual_area == expected_area and rot_metrics.get("scrollWidth", 0) <= rot_metrics.get("clientWidth", -1),
                       {"first_line": actual_name, "expected_first_line": rot_title, "second_line": actual_area,
                        "expected_second_line": expected_area, "series_areas": unique(image.get("area") for image in rot_images),
                        "series_places": unique(image.get("place") for image in rot_images), "first_line_metrics": rot_metrics})
        if width in (375, 1440):
            evidence.screenshot(page, f"{width}/series-australia-se3-rottnest.png", locator=page.locator("[data-series]"))


def _run_visible_navigation(page, visible_ids: list[str], studies: dict[str, dict], evidence: Evidence):
    # Each visible row click is exercised against the real worklist, followed by
    # a fresh real page navigation so no fixture or app state is injected.
    for sid in visible_ids:
        study = studies.get(sid)
        if not study:
            evidence.check(f"navigation.visible-study-click.{sid}", False, {"error": "study missing from source"})
            continue
        try:
            _open_route(page, "")
            row = page.locator(f'.oz-row[href="#{sid}"]')
            if row.count() != 1:
                evidence.check(f"navigation.visible-study-click.{sid}", False, {"error": "worklist row missing", "count": row.count()})
                continue
            row.click()
            page.wait_for_function("matchMedia('(min-width: 900px)').matches || document.body.classList.contains('is-reading')", timeout=10000)
            index = first_se_index(study, 1)
            if index is None:
                evidence.check(f"navigation.visible-study-click.{sid}", False, {"error": "no SE1 image"})
                continue
            _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
            actual = _active_source(page)
            expected = study["images"][index].get("src")
            evidence.check(f"navigation.visible-study-click.{sid}", actual == expected,
                           {"study_id": sid, "actual": actual, "expected_first_se1": expected, "se1_index": index})
        except Exception as exc:
            evidence.failed_exception(f"navigation.visible-study-click.{sid}", exc)

    # Native canonical deep links cover every source study, including historical
    # studies filtered off the current worklist; visibility is not route deletion.
    for sid, study in studies.items():
        if not study:
            continue
        try:
            _open_route(page, f"#{sid}")
            index = first_se_index(study, 1)
            if index is None:
                evidence.check(f"navigation.all-study-plain-hash.{sid}", False, {"error": "no SE1 image"})
                continue
            _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
            actual = _active_source(page)
            expected = study["images"][index].get("src")
            evidence.check(f"navigation.all-study-plain-hash.{sid}", actual == expected,
                           {"actual": actual, "expected_first_se1": expected, "se1_index": index})
        except Exception as exc:
            evidence.failed_exception(f"navigation.all-study-plain-hash.{sid}", exc)

    # P and N browse the real visible-study list; each transition must start at
    # that destination's first ordinary SE1 image, not its scout cover.
    if not visible_ids:
        evidence.check("navigation.pn-all-visible-studies", False, {"error": "empty recentStudyIds"})
        return
    for key, start_id, direction in (("N", visible_ids[0], 1), ("P", visible_ids[-1], -1)):
        try:
            _open_route(page, f"#{start_id}")
            for step in range(len(visible_ids)):
                current_pos = visible_ids.index(start_id) if step == 0 else (visible_ids.index(start_id) + direction * step) % len(visible_ids)
                destination = visible_ids[(current_pos + direction) % len(visible_ids)]
                page.keyboard.press(key)
                dest = studies.get(destination)
                index = first_se_index(dest, 1) if dest else None
                if index is None:
                    evidence.check(f"navigation.{key}-visible.{step:03d}", False, {"destination": destination, "error": "missing first SE1"})
                    continue
                page.wait_for_function("matchMedia('(min-width: 900px)').matches || document.body.classList.contains('is-reading')", timeout=5000)
                _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
                actual = _active_source(page)
                expected = dest["images"][index].get("src")
                evidence.check(f"navigation.{key}-visible.{step:03d}", actual == expected,
                               {"from": start_id if step == 0 else visible_ids[current_pos], "to": destination,
                                "actual": actual, "expected_first_se1": expected})
        except Exception as exc:
            evidence.failed_exception(f"navigation.{key}-visible-sequence", exc)


def _run_historical_routes(page, data: dict, focus: dict[str, dict | None], evidence: Evidence):
    cases, unavailable_reason = _baseline_routes_for_focus(data, focus)
    # Numbered routes retain image identity; bare study/alias opens now use SE1.
    cases = [case for case in cases if "/" in case["fragment"]]
    if unavailable_reason:
        evidence.check("routing.baseline-explicit-image-ledger", True, {"status": "SKIP", "reason": unavailable_reason})
        return
    evidence.report["baseline_explicit_route_count"] = len(cases)
    if not cases:
        evidence.check("routing.baseline-explicit-image-ledger", False, {"error": "baseline exists but yielded no focus routes"})
        return
    result = _serve_route_cases(page, cases)
    evidence.check("routing.explicit-image-routes-retain-original-source", result["checked"] == len(cases) and not result["failures"],
                   {"baseline_revision": BASELINE_REV, **result, "sample": cases[:5]})
    evidence.write()


def _page_events(page, evidence: Evidence, label: str):
    page.on("pageerror", lambda error: evidence.report["page_errors"].append({"page": label, "error": str(error)}))


def test_outside_place_series_real_data_acceptance():
    evidence = Evidence(EVIDENCE)
    try:
        data = json.loads(DATA_PATH.read_text())
        evidence.report["source_sha256"] = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
        evidence.report["source_study_count"] = len(data.get("studies", []))
        evidence.report["source_image_count"] = sum(len(study.get("images", [])) for study in data.get("studies", []))
        evidence.report["study_table"] = make_study_table(data)
        studies_by_id = {study.get("id"): study for study in data.get("studies", [])}
        focus = focus_studies(data)
        _evaluate_data_requirements(data, focus, evidence)
    except Exception as exc:
        evidence.failed_exception("data.load-and-validate", exc)
        evidence.report["status"] = "FAIL"
        evidence.write()
        raise

    try:
        playwright = sync_playwright().start()
        browser_type = getattr(playwright, BROWSER_NAME)
        browser = browser_type.launch(headless=True)
        evidence.report["browser_version"] = browser.version
        evidence.report["browser_name"] = BROWSER_NAME
        evidence.write()
    except Exception as exc:
        evidence.failed_exception("browser.launch", exc)
        evidence.report["status"] = "FAIL"
        evidence.write()
        raise

    try:
        runtime_checked = False
        for width, height in ((375, 812), (1024, 900), (1440, 1000)):
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", device_scale_factor=1)
            page = context.new_page()
            _page_events(page, evidence, f"worklist-{width}")
            try:
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function("document.body.classList.contains('is-ready')", timeout=20000)
                page.wait_for_function("document.querySelector('#oz-data')?.textContent?.length > 0", timeout=15000)
                runtime = json.loads(page.locator("#oz-data").text_content() or "{}")
                if not runtime_checked:
                    runtime_base = {key: runtime.get(key) for key in ("studies", "aliases")}
                    source_base = {key: data.get(key) for key in ("studies", "aliases")}
                    runtime_base["studies"] = sorted(runtime_base["studies"], key=lambda s: s["id"])
                    source_base["studies"] = sorted(source_base["studies"], key=lambda s: s["id"])
                    evidence.check("browser.real-payload-matches-source", _same_json(runtime_base, source_base),
                                   {"runtime_studies": len(runtime_base.get("studies") or []), "source_studies": len(source_base.get("studies") or []),
                                    "runtime_aliases": len(runtime_base.get("aliases") or {}), "source_aliases": len(source_base.get("aliases") or {}),
                                    "runtime_payload_sha256": hashlib.sha256(json.dumps(runtime_base, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                                    "source_payload_sha256": hashlib.sha256(json.dumps(source_base, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
                    runtime_checked = True
                visible_ids = runtime.get("recentStudyIds", [])
                evidence.report.setdefault("visible_study_ids", visible_ids)
                hidden_ids = {study.get("id") for study in data.get("studies", []) if study.get("hidden") is True or str(study.get("status", "")).upper() == "HIDDEN"}
                visible_ids_valid = isinstance(visible_ids, list) and len(visible_ids) == len(set(visible_ids)) and all(sid in studies_by_id and sid not in hidden_ids for sid in visible_ids)
                evidence.check(f"worklist.visible-count-matches-payload.{width}", isinstance(visible_ids, list) and page.locator(".oz-row").count() == len(visible_ids) and visible_ids_valid,
                               {"rows": page.locator(".oz-row").count(), "recentStudyIds": len(visible_ids) if isinstance(visible_ids, list) else None,
                                "duplicate_visible_ids": len(visible_ids) - len(set(visible_ids)) if isinstance(visible_ids, list) else None,
                                "hidden_ids": sorted(hidden_ids), "unexpected_visible_hidden_ids": sorted(hidden_ids.intersection(visible_ids)) if isinstance(visible_ids, list) else []})
                evidence.screenshot(page, f"{width}/worklist-full.png", full_page=True)
                for sid in visible_ids if isinstance(visible_ids, list) else []:
                    study = studies_by_id.get(sid)
                    if study:
                        try:
                            _worklist_row_checks(page, study, evidence, width)
                        except Exception as exc:
                            evidence.failed_exception(f"worklist.row-checks.{width}.{sid}", exc)
                for key in ("pakistan", "galapagos", "southwest", "australia"):
                    study = focus.get(key)
                    if not study:
                        evidence.check(f"worklist.required-row-present.{width}.{key}", False, {"error": "source study missing"})
                        continue
                    row = page.locator(f'.oz-row[href="#{study["id"]}"]')
                    visible = row.count() == 1 and row.is_visible()
                    evidence.check(f"worklist.required-row-present.{width}.{key}", visible, {"study_id": study["id"], "rows": row.count()})
                    if visible and width in (375, 1440):
                        _capture_row(page, row, key, evidence, width)
                montreal = focus.get("montreal")
                if montreal:
                    montreal_row = page.locator(f'.oz-row[href="#{montreal["id"]}"]')
                    if montreal_row.count() == 1:
                        actual_country_line = montreal_row.locator(".oz-region").inner_text().strip()
                        country_ok = actual_country_line.startswith("Canada")
                    else:
                        actual_country_line = location_line(montreal)
                        country_ok = actual_country_line == "Canada" and montreal_row.count() == 0
                    evidence.check(f"worklist.montreal-canada-or-remains-hidden.{width}", country_ok,
                                   {"study_id": montreal["id"], "row_present": montreal_row.count() == 1,
                                    "area_line": actual_country_line, "hidden_by_recent_list": montreal["id"] not in visible_ids})
                context.close()
            except Exception as exc:
                evidence.failed_exception(f"browser.worklist-viewport.{width}", exc)
                context.close()

        # Focused reader interactions and mobile/desktop overlay geometry.
        for width, height in ((375, 812), (1440, 1000)):
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", device_scale_factor=1)
            page = context.new_page()
            _page_events(page, evidence, f"reader-{width}")
            try:
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_function("document.body.classList.contains('is-ready')", timeout=20000)
                for key in ("pakistan", "australia", "galapagos", "southwest"):
                    study = focus.get(key)
                    if study:
                        try:
                            _open_route(page, f"#{study['id']}")
                            index = first_se_index(study, 1)
                            if index is None:
                                evidence.check(f"series.strip-has-se1.{width}.{key}", False, {"error": "no first SE1 image"})
                            else:
                                _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
                                _check_series_strip(page, study, evidence, key, width)
                        except Exception as exc:
                            evidence.failed_exception(f"series.strip-check.{width}.{key}", exc)
                for key in ("pakistan", "australia"):
                    study = focus.get(key)
                    if study:
                        try:
                            _run_overlay_acceptance(page, key, study, evidence, width)
                        except Exception as exc:
                            evidence.failed_exception(f"overlay.workflow.{width}.{key}", exc)
                southwest = focus.get("southwest")
                if southwest and southwest.get("images"):
                    last = southwest["images"][-1]
                    _open_route(page, f"#{southwest['id']}/{len(southwest['images'])}")
                    _wait_image(page, page.locator("[data-cells] img").first.get_attribute("data-want") or "")
                    evidence.check(f"southwest.last-image-hoover-dam.{width}", _active_source(page) == last.get("src") and last.get("place") == "Hoover Dam",
                                   {"actual_source": _active_source(page), "expected_source": last.get("src"), "place": last.get("place")})
                    _check_overlay(page, southwest, last, evidence, "southwest", width, "last-hoover-dam")
                    if width in (375, 1440):
                        evidence.screenshot(page, f"{width}/overlay-southwest-last-hoover-dam.png")
                context.close()
            except Exception as exc:
                evidence.failed_exception(f"browser.reader-viewport.{width}", exc)
                context.close()

        # Every visible study is opened from its row, plain hash and both P/N
        # browser shortcuts. This is a separate run so screenshots remain worklist-focused.
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce", device_scale_factor=1)
        page = context.new_page()
        _page_events(page, evidence, "all-visible-navigation")
        try:
            _open_route(page, "")
            runtime = json.loads(page.locator("#oz-data").text_content() or "{}")
            visible_ids = runtime.get("recentStudyIds", [])
            _run_visible_navigation(page, visible_ids, studies_by_id, evidence)
            _run_historical_routes(page, data, focus, evidence)
        except Exception as exc:
            evidence.failed_exception("browser.all-visible-navigation", exc)
        finally:
            context.close()

        if evidence.report["page_errors"]:
            evidence.check("browser.no-page-errors", False, evidence.report["page_errors"])
        else:
            evidence.check("browser.no-page-errors", True, [])
    finally:
        try:
            browser.close()
        finally:
            playwright.stop()

    evidence.report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    evidence.report["failure_count"] = len(evidence.failures)
    evidence.report["status"] = "PASS" if not evidence.failures else "FAIL"
    evidence.report["failed_checks"] = evidence.failures
    evidence.write()
    assert not evidence.failures, f"Outside real-data acceptance failed; see {EVIDENCE / 'acceptance-receipt.json'} ({len(evidence.failures)} failed checks)"
