#!/usr/bin/env python3
"""Add image-level locations and date/place series to Outside Studies.

GPS is joined by canonical public src -> private source asset ref -> archive index.
Coordinates and join identifiers are written only to the private assignment ledger.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "src/data/outside-studies.json"
DEFAULT_SOURCE_MAP = Path("/home/ubuntu/scratch/2026-10-04-outside-owner-review/bundle/source-ref-map.private.json")
DEFAULT_ARCHIVE_INDEX = Path("/home/ubuntu/scratch/2026-10-03-outside-trip-expansion/discovery/index.jsonl")
DEFAULT_MONTREAL_DELTA = Path("/home/ubuntu/scratch/2026-10-04-outside-owner-review/montreal-november-album-gap/preparation/source-bound-delta.private.json")
DEFAULT_PRIVATE_DIR = Path("/home/ubuntu/scratch/2026-10-05-outside-place-series/data")
DEFAULT_BASELINE = DEFAULT_PRIVATE_DIR / "outside-studies.before.json"

FOCUS_IDS = {
    "new-zealand-2026-july-photos-161007",
    "australia-2026-july-gallery-20261005-161007",
    "pakistan-2026-summer-gallery-20261005",
    "galapagos-2026-january-photos-20261004-20261005-161007",
    "montreal-november-2025-photos-20261005",
    "american-southwest-2025-october-gallery-20261004-2-20261005",
}
AUSTRALIA_ID = "australia-2026-july-gallery-20261005-161007"
PAKISTAN_ID = "pakistan-2026-summer-gallery-20261005"
TRANSIT_PLACES = {
    "Bangkok",
    "Rome",
    "Albania",
}
STUDY_SCOPED_NO_GPS = {
    "sams-point-2025-august": {
        "place": "Sam’s Point",
        "evidence": "Existing canonical study ID and title identify the Sam’s Point Ice Caves outing; no GPS-bound image exists in this study.",
    },
    "maryland-national-harbor-2023-august": {
        "place": "National Harbor",
        "evidence": "Existing canonical study ID and title identify National Harbor; no GPS-bound image exists in this study.",
    },
    "montreal-august-2023-photos": {
        "place": "Montréal",
        "evidence": "Existing canonical study place and dated Montréal series titles; no GPS-bound image exists in this study.",
    },
    "point-lookout-2015-august": {
        "place": "Point Lookout",
        "evidence": "Existing canonical image source path `/outside/point-lookout/` and coastal-overlook series title; no GPS-bound image exists in this study.",
    },
    "europe-shared-album": {
        "place": "Location unconfirmed",
        "evidence": "No per-image GPS or independently supported city exists for this hidden shared album; 17 frames also lack capture dates. A nearest-time GPS assignment cannot be established, so the city is explicitly unconfirmed rather than inherited from the study title.",
    },
}

# Only normalize a GPS-reported subcity/neighborhood when the coordinate supports
# the parent/landmark. Other actual towns remain individually named.
CITY_NORMALIZATIONS = {
    "Busselton city centre": "Busselton",
    "East Perth": "Perth",
    "West Perth": "Perth",
    "Perth city centre": "Perth",
    "Ohinemutu": "Rotorua",
    "Reporoa": "Rotorua",
    "Lat Krabang": "Bangkok",
    "Vatican City": "Rome",
    "Prezë": "Albania",
    "Mughalabad": "Murree",
    "Gnarabup": "Margaret River",
    "Springdale": "Zion",
    "Twentynine Palms": "Joshua Tree",
    "Indio Hills": "Joshua Tree",
    "Tusayan": "Grand Canyon",
    "Boulder City": "Hoover Dam",
    "Druid Hills": "Atlanta",
    "Paradise": "Las Vegas",
    "Celebration": "Orlando",
    "Indian Hills": "Denver",
    "Bala Cynwyd": "Philadelphia",
    "Ville-Marie": "Montréal",
    "Mercier–Hochelaga-Maisonneuve": "Montréal",
}

PREFERRED = {
    "new-zealand-2026-july-photos-161007": {"Auckland", "Rotorua"},
    AUSTRALIA_ID: {"Bangkok", "Busselton", "Fremantle", "Rottnest Island", "Perth"},
    PAKISTAN_ID: {"Rome", "Albania", "Karachi", "Islamabad", "Murree", "Lahore"},
    "galapagos-2026-january-photos-20261004-20261005-161007": {"Santa Cruz", "Isabela", "San Cristóbal"},
    "montreal-november-2025-photos-20261005": {"Montréal"},
    "american-southwest-2025-october-gallery-20261004-2-20261005": {"Joshua Tree", "Las Vegas", "Grand Canyon", "Zion", "Hoover Dam"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gps_row(row: dict | None) -> bool:
    if not row:
        return False
    raw_lat, raw_lon = row.get("latitude"), row.get("longitude")
    if raw_lat is None or raw_lon is None:
        return False
    try:
        lat, lon = float(raw_lat), float(raw_lon)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180


def normalized_city(row: dict) -> str | None:
    city = row.get("city")
    if not isinstance(city, str) or not city.strip():
        return None
    city = city.strip()
    if city in CITY_NORMALIZATIONS:
        return CITY_NORMALIZATIONS[city]
    return city


def place_from_gps(study_id: str, row: dict) -> tuple[str, bool, str]:
    lat, lon = float(row["latitude"]), float(row["longitude"])
    country = (row.get("country") or "").casefold()
    city = (row.get("city") or "").strip()

    if study_id == "new-zealand-2026-july-photos-161007":
        if -38.38 < lat < -38.32 and 176.34 < lon < 176.40:
            return "Waiotapu", False, "GPS cluster is at the separately named Waiotapu settlement, 0.6–2.3 km from its mapped centre versus 25–27 km from Rotorua; OSM node 4020632424. Raw Reporoa is not used."
        if lat > -37.5 and lon > 172:
            return "Auckland", False, "GPS coordinates place the frame in Auckland."
        return "Rotorua", False, "GPS coordinates place the frame in Rotorua city or its Ohinemutu suburb; Waiotapu is classified separately."

    if study_id == AUSTRALIA_ID:
        if -34.24 < lat < -34.20 and 115.01 < lon < 115.05:
            return "Hamelin Bay", False, "GPS is within the separately named Hamelin Bay settlement, 0.3–0.6 km from its mapped centre versus about 16 km from Augusta; OSM relation 11688650. Retained for owner confirmation."
        if "thailand" in country or lat > 0:
            return "Bangkok", True, "GPS coordinates place the frame at Bangkok airport/Lat Krabang; authorized transit stop."
        if city in {"Perth", "Perth city centre", "East Perth", "West Perth"} or (lat < -31.5 and lon > 115.7):
            return "Perth", False, "GPS coordinates place the frame in metropolitan Perth; city-centre and East/West Perth labels are normalized to Perth."
        place = normalized_city(row)
        if place:
            return place, False, f"Exact mapped GPS point; retained real town/island `{city}` or normalized its geocoder subcity label."
        if -33.9 < lat < -33.3 and 115.0 < lon < 115.5:
            return "Busselton", False, "GPS coordinates place the frame in the Busselton/Dunsborough/Yallingup corridor; nearest named town Busselton."
        raise ValueError(f"Unclassified Australian GPS coordinate for {row.get('asset_id')}: {lat},{lon}")

    if study_id == PAKISTAN_ID:
        if 34.04 < lat < 34.12 and 73.38 < lon < 73.43:
            return "Nathia Gali", False, "GPS is near Nathia Gali town (OSM node 366079598), not the incorrectly indexed Dhirkot administrative area farther east. Retained as an unlisted separate town."
        if "italy" in country or "holy see" in country or city in {"Rome", "Vatican City"}:
            return "Rome", True, "Exact mapped GPS point is in Rome/Vatican City; authorized transit stop."
        if "albania" in country or city == "Prezë":
            return "Albania", True, "Exact mapped GPS point is in Albania; authorized transit stop."
        place = normalized_city(row)
        if place:
            return place, False, f"Exact mapped GPS point; retained the named town or normalized `{city}` to nearest listed town Murree."
        raise ValueError(f"Unclassified Pakistan GPS coordinate for {row.get('asset_id')}: {lat},{lon}")

    if study_id == "galapagos-2026-january-photos-20261004-20261005-161007":
        if lon < -90.55:
            return "Isabela", False, "GPS longitude places the frame on Isabela Island."
        if lon > -89.8:
            return "San Cristóbal", False, "GPS longitude places the frame on San Cristóbal Island."
        return "Santa Cruz", False, "GPS longitude places the frame on Santa Cruz Island; used island geography even when reverse-geocoder city is blank."

    if study_id == "montreal-november-2025-photos-20261005":
        return "Montréal", False, "Exact mapped GPS point lies within Montréal; Mercier–Hochelaga-Maisonneuve and Ville-Marie are normalized to the city."

    if study_id == "american-southwest-2025-october-gallery-20261004-2-20261005":
        if lon < -115.5 and lat < 35:
            return "Joshua Tree", False, "GPS coordinates place the frame at Joshua Tree National Park / its immediate gateway communities."
        if lon < -114.0:
            return "Hoover Dam", False, "GPS coordinates place the frame at Hoover Dam; Boulder City is the nearest geocoder city."
        if 35.5 <= lat <= 36.8 and -113.5 <= lon <= -111.5:
            return "Grand Canyon", False, "GPS coordinates place the frame in Grand Canyon National Park / East Rim; Tusayan or blank geocoder city is not used as the display label."
        if lat > 36.8 and -113.5 <= lon <= -111.5:
            return "Zion", False, "GPS coordinates place the frame in Zion National Park; Springdale is normalized to the park."
        raise ValueError(f"Unclassified Southwest GPS coordinate for {row.get('asset_id')}: {lat},{lon}")

    place = normalized_city(row)
    if place:
        return place, False, f"Exact mapped GPS point; used reverse-geocoder city `{city}` after the known subcity normalization rules."

    # No raw city is exposed for GPS points lacking a reverse-geocoder label.
    # These only occur in regions with an unambiguous study-specific geography.
    if study_id == "puerto-rico-2025-october":
        return "San Juan", False, "Exact mapped GPS point in the San Juan metropolitan area; geocoder city field is blank."
    if study_id == "colorado-2025-july-photos":
        return "Denver", False, "Exact mapped GPS point in the Denver/Boulder Front Range; nearest named city among this study’s GPS locations is Denver."
    raise ValueError(f"GPS row has no usable display city for {study_id} / {row.get('asset_id')}: {lat},{lon}")


def image_instant(image: dict, study: dict) -> dt.datetime | None:
    day = image.get("d")
    if not day:
        return None
    try:
        date = dt.date.fromisoformat(day)
    except (TypeError, ValueError):
        return None
    time = image.get("t") or "00:00:00"
    try:
        clock = dt.time.fromisoformat(time)
    except (TypeError, ValueError):
        clock = dt.time()
    zone_text = image.get("tz") or study.get("tz") or ""
    match = re.search(r"UTC\s*([+\-−])\s*(\d{1,2})(?::?(\d{2}))?", zone_text)
    if match:
        sign = -1 if match.group(1) in {"-", "−"} else 1
        offset = dt.timedelta(hours=int(match.group(2)), minutes=int(match.group(3) or 0)) * sign
        return dt.datetime.combine(date, clock).replace(tzinfo=dt.timezone(offset)).astimezone(dt.timezone.utc)
    # Missing offsets use UTC as a deterministic ordering basis; explicit image offsets always win.
    return dt.datetime.combine(date, clock).replace(tzinfo=dt.timezone.utc)


def nearest_anchor(image: dict, study: dict, anchors: list[dict]) -> tuple[dict, str]:
    instant = image_instant(image, study)
    scored = []
    for anchor in anchors:
        anchor_instant = image_instant(anchor["image"], study)
        if instant is not None and anchor_instant is not None:
            scored.append((abs((instant - anchor_instant).total_seconds()), anchor["index"], anchor))
    if scored:
        seconds, _, anchor = min(scored, key=lambda item: (item[0], item[1]))
        minutes = int(seconds // 60)
        return anchor, f"Nearest in time (absolute offset {minutes} minutes) to a GPS-mapped image in this same study."
    anchor = min(anchors, key=lambda item: (abs(item["index"] - image["_index"]), item["index"]))
    return anchor, "Capture timestamps unavailable for a time comparison; nearest source-order GPS-mapped image in this same study."


def date_group_series(study: dict, old_series: list[dict]) -> list[dict]:
    images = study["images"]
    transit_count = sum(1 for image in images if image["transit"])
    if transit_count and any(not image["transit"] for image in images[:transit_count]):
        raise ValueError(f"Transit images are not at the beginning of {study['id']}; refusing to reorder source identities.")
    if any(image["transit"] for image in images[transit_count:]):
        raise ValueError(f"Transit images are not one initial block in {study['id']}; refusing to reorder source identities.")

    groups: list[tuple[int, int, int]] = []
    if transit_count:
        groups.append((0, transit_count, 0))
    number = 1
    index = transit_count
    while index < len(images):
        first = images[index]
        pair = (first.get("d", ""), first["place"])
        end = index + 1
        while end < len(images) and not images[end]["transit"] and (images[end].get("d", ""), images[end]["place"]) == pair:
            end += 1
        groups.append((index, end - index, number))
        number += 1
        index = end

    result = []
    for start, count, display_number in groups:
        segment = images[start:start + count]
        series: dict = {
            "start": start,
            "count": count,
            "time": segment[0].get("t", ""),
            "key": study["key"] if study["key"] in range(start, start + count) else start,
            "displayNumber": display_number,
        }
        series["date"] = segment[0].get("d", "")
        series["dateEnd"] = segment[-1].get("d", series["date"])
        prior = next((item for item in old_series if item["start"] <= start < item["start"] + item["count"]), None)
        if display_number == 0:
            series["title"] = "SCOUT · " + ", ".join(dict.fromkeys(image["place"] for image in segment))
        elif prior and prior.get("title"):
            series["title"] = prior["title"]
        for image in segment:
            image["se"] = display_number
        result.append(series)
    return result


def format_place_series(studies: list[dict]) -> str:
    out = ["# Outside Studies — exact date/place series tables", "", "Generated by `scripts/migrate_outside_place_series.py` from the public JSON and private archive index.", "", "Transit is shown as SE 0 and excluded from each study-level date range. Counts are exact image-record counts. Coordinates and private asset IDs are not included.", ""]
    for study in studies:
        out.extend([f"## {study['place']} (`{study['id']}`)", "", f"Study range: {study.get('date', '')}" + (f" – {study['dateEnd']}" if study.get("dateEnd") and study.get("dateEnd") != study.get("date") else "") + f" · {len(study['images'])} images", "", "| SE | Date | Place | Images | JSON indexes (0-based) | Source span |", "|---:|---|---|---:|---|---|"])
        for series in sorted(study["series"], key=lambda item: item["start"]):
            segment = study["images"][series["start"]:series["start"] + series["count"]]
            places = list(dict.fromkeys(image["place"] for image in segment))
            dates = [image.get("d", "") for image in segment if image.get("d")]
            date_label = ""
            if dates:
                date_label = dates[0] if dates[0] == dates[-1] else f"{dates[0]} – {dates[-1]}"
            place_label = " · ".join(places)
            if series["displayNumber"] == 0:
                place_label = "Scout · " + ", ".join(places) + " (transit)"
            source_span = f"`{segment[0]['src']}` → `{segment[-1]['src']}`"
            index_label = f"{series['start']}–{series['start'] + series['count'] - 1}"
            out.append(f"| {series['displayNumber']} | {date_label} | {place_label} | {series['count']} | {index_label} | {source_span} |")
        out.extend([""])
    return "\n".join(out).rstrip() + "\n"


def format_exceptions(assignments: list[dict], studies: list[dict], input_hashes: dict) -> str:
    out = [
        "# Outside Studies — assignment exceptions and provenance",
        "",
        "Status: DATA COMPLETE — parent/UI acceptance pending; generated by `scripts/migrate_outside_place_series.py`.",
        "",
        "## Provenance and date caveats",
        "",
        f"- Exact canonical-src → private asset-ref → archive-index GPS join: {sum(row['method'] == 'exact-gps' for row in assignments)} image rows. Index SHA-256: `{input_hashes['archive_index_sha256']}`; source-ref map SHA-256: `{input_hashes['source_ref_map_sha256']}`.",
        f"- Six focus studies contain 232 images: {sum(row['method'] == 'exact-gps' for row in assignments if row['study_id'] in FOCUS_IDS)} exact map+GPS joins; the other 18 are 8 source-map-unbound legacy images (4 Pakistan, 4 Southwest) and 10 Montréal shared-album renditions without GPS. All 18 use the nearest-in-time GPS-bearing image in the same study; each source and anchor is listed below.",
        "- The eight unbound legacy sources are Pakistan `/outside/ayubia/015`, `/outside/ayubia/031`, `/outside/lahore/034`, `/outside/lahore/038`; Southwest `/outside/zion/010`, `/outside/zion/020`, `/outside/assets/utah-night-sky-2025/utah-night-sky-01`, `/outside/hoover-dam/020`.",
        "- The archive index supplies GPS and capture-date/time values; its capture dates are not native-EXIF corroboration for every selected image. Do not describe those dates as independently verified source EXIF.",
        "- The previous exact-map audit recorded 213/214 public local timestamps matching indexed capture time to the second. `/outside/hoover-dam/017` remains unchanged at public `2025-10-14 12:52:40 UTC−07:00`; archive-derived local time was `12:42:02 UTC−07:00`. No date/time/tz values were changed.",
        "- Galápagos current-row identity remains imperfectly resolved: earlier exact-asset checks corroborated GPS on an actual JPEG sample, but that sample’s native DateTimeOriginal did not corroborate the indexed capture date. No current-row date/time was revised.",
        "- The 10 Montréal Nov 2025 album-rendered images have no GPS. Their private supplemental artifact reports rendition metadata only (nine native DateTimeOriginal values, zero GPS, original-file identity not claimed). Place was assigned from the nearest-in-time GPS-bearing image in the same study.",
        "- Public `outside-studies.json` contains display place/transit/SE only; this private file and the private row ledger hold provenance. No GPS coordinates or private IDs are published.",
        "",
        "## Nearest-time assignments (no per-image GPS join)",
        "",
        "Each row below is assigned the displayed place of its nearest-in-time GPS-bound image in the same study. Timestamp ties resolve to the earlier source-order anchor. Where a study has no GPS-bound images, see the separate weak-evidence list below.",
        "",
        "| Study | Source identifier (`src`) | Assigned place | Nearest GPS-bound source | Evidence |",
        "|---|---|---|---|---|",
    ]
    for row in assignments:
        if row["method"] != "nearest-time-no-gps":
            continue
        anchor = row.get("anchor_src") or ""
        out.append(f"| `{row['study_id']}` | `{row['src']}` | {row['place']} | `{anchor}` | {row['evidence']} |")
    out.extend(["", "## Whole-study no-GPS assignments — weak scoped evidence", "", "No study-level location fallback is used at rendering time: each image has an explicit `place`. The following assignments are necessarily broad or title/path-derived because these entire studies have no GPS-bound image.", "", "| Study | Source identifier (`src`) | Assigned place | Evidence |", "|---|---|---|---|"])
    for row in assignments:
        if row["method"] != "study-scoped-no-gps":
            continue
        out.append(f"| `{row['study_id']}` | `{row['src']}` | {row['place']} | {row['evidence']} |")
    out.extend(["", "## Unlisted separate towns in the six focus studies", "", "Per the owner instruction, distinct towns remain individually named rather than being collapsed into a nearby listed parent. These are the display names outside each study’s preferred-place list; confirm them if a stricter preferred list is intended.", "", "| Study | Unlisted place | Exact source identifiers (`src`) |", "|---|---|---|"])
    by_id = {study["id"]: study for study in studies}
    for study_id, preferred in PREFERRED.items():
        study = by_id[study_id]
        places = list(dict.fromkeys(image["place"] for image in study["images"] if image["place"] not in preferred and not image["transit"]))
        for place in places:
            sources = [image["src"] for image in study["images"] if image["place"] == place]
            out.append(f"| `{study_id}` | {place} | " + ", ".join(f"`{src}`" for src in sources) + " |")
    out.extend(["", "## GPS interpretation exceptions", "", "- New Zealand: eight raw `Reporoa` points are at the separate Waiotapu settlement, not Rotorua city; they now read Waiotapu. Ohinemutu is a Rotorua suburb and reads Rotorua. Waiotapu is a small settlement/hamlet retained for confirmation, not a raw district name.", "- Australia `Lat Krabang` is normalized to Bangkok (transit); Perth city centre/East Perth/West Perth to Perth; Busselton city centre to Busselton; Gnarabup locality to nearest town Margaret River. Dunsborough, Yallingup, Margaret River, and Augusta remain separate town names. Two Hamelin Bay settlement frames are separated from Augusta and flagged for confirmation. Cape Leeuwin and Cape Naturaliste landmarks retain nearest-town Augusta and Dunsborough; Gnarabup is normalized to Margaret River.", "- Pakistan Rome/Vatican City is one Rome transit series; Prezë is Albania transit. Mughalabad is normalized to Murree. Two raw Dhirkot GPS rows actually lie near Nathia Gali, and the no-GPS Ayubia frame inherits Nathia Gali from its nearest-time anchor. Retained photos first show Islamabad on Jul 4, after Murree/Nathia Gali; dates and first-visit order are not fabricated to match the suggested itinerary.", "- Galápagos Puerto Ayora/Puerto Villamil/Puerto Baquerizo Moreno map to the GPS-bearing islands Santa Cruz/Isabela/San Cristóbal. One blank-city row uses GPS longitude for Santa Cruz.", "- Southwest GPS is mapped to Joshua Tree, Grand Canyon, Zion, or Hoover Dam by coordinates/park geography, not geocoder city. No GPS point in this study supports Las Vegas, so none is invented.", "", "| Study | Reverse-geocoder city | Assigned place | Source identifier (`src`) |", "|---|---|---|---|"])
    rules = {
        "new-zealand-2026-july-photos-161007": {"Reporoa", "Ohinemutu"},
        AUSTRALIA_ID: {"Lat Krabang", "East Perth", "West Perth", "Perth city centre", "Busselton city centre", "Gnarabup"},
        PAKISTAN_ID: {"Vatican City", "Prezë", "Mughalabad", "Dhirkot"},
        "galapagos-2026-january-photos-20261004-20261005-161007": {"Puerto Ayora", "Puerto Villamil", "Puerto Baquerizo Moreno", ""},
        "american-southwest-2025-october-gallery-20261004-2-20261005": {"Springdale", "Twentynine Palms", "Indio Hills", "Tusayan", "Boulder City", ""},
    }
    for study_id, raw_cities in rules.items():
        rows = [row for row in assignments if row["study_id"] == study_id and row.get("raw_city", "") in raw_cities and row["method"] == "exact-gps"]
        for row in rows:
            out.append(f"| `{study_id}` | {row.get('raw_city') or '(blank)'} | {row['place']} | `{row['src']}` |")
    out.extend(["", "## Transit and study-key handling", "", "- Australia (Bangkok), Pakistan (Rome/Albania), and the inherited hidden Cruise (Merritt Island) scout have transit images. Each transit record is retained at its original image index, flagged `transit: true`, and assigned `se: 0`; all transit frames are one leading series each.", "- Australia/Pakistan `study.key` previously pointed to a transit scout at index 0. It now points to the first ordinary SE 1 image so the study key is never the SE 0 scout. No image moved and no source/deep-link alias changed.", "- All other images are non-transit; every study uses maximal consecutive date/place groups, with non-transit display numbers starting at 1. Legacy titles are not used as location labels.", ""])
    return "\n".join(out)


def migrate(data_path: Path, source_map_path: Path, index_path: Path, montreal_delta_path: Path | None, baseline_path: Path, out_path: Path, private_dir: Path, check: bool = False) -> dict:
    data = json.loads(data_path.read_text())
    baseline = json.loads(baseline_path.read_text())
    if [study["id"] for study in data["studies"]] != [study["id"] for study in baseline["studies"]]:
        raise ValueError("Study identities/order differ from the frozen pre-migration snapshot")
    if data["aliases"] != baseline["aliases"]:
        raise ValueError("Route aliases differ from the frozen pre-migration snapshot")
    for study, original in zip(data["studies"], baseline["studies"]):
        if [image["src"] for image in study["images"]] != [image["src"] for image in original["images"]]:
            raise ValueError(f"Image identities/order differ from the frozen pre-migration snapshot: {study['id']}")
        current_dates = [[image.get("d"), image.get("t"), image.get("tz")] for image in study["images"]]
        original_dates = [[image.get("d"), image.get("t"), image.get("tz")] for image in original["images"]]
        if current_dates != original_dates:
            raise ValueError(f"Published date/time/timezone values differ from the frozen pre-migration snapshot: {study['id']}")
    source_map = json.loads(source_map_path.read_text())
    source_rows = source_map.get("source_rows", [])
    source_ref_by_src: dict[str, dict] = {}
    for row in source_rows:
        src = row.get("canonical_src")
        if src:
            if src in source_ref_by_src and source_ref_by_src[src].get("asset_id") != row.get("asset_id"):
                raise ValueError(f"Ambiguous source-ref map for {src}")
            source_ref_by_src[src] = row

    index_rows = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
    index_by_asset: dict[str, dict] = {}
    for row in index_rows:
        index_by_asset[row["asset_id"]] = row
        for asset_id in row.get("source_asset_ids", []):
            index_by_asset[asset_id] = row

    montreal_delta_hash = sha256(montreal_delta_path) if montreal_delta_path and montreal_delta_path.exists() else None
    source_path_to_index_row = {}
    for study in data["studies"]:
        for image in study["images"]:
            ref = source_ref_by_src.get(image["src"])
            asset_id = ref.get("asset_id") if ref else None
            source_path_to_index_row[image["src"]] = index_by_asset.get(asset_id) if asset_id else None

    assignments: list[dict] = []
    study_anchors: dict[str, list[dict]] = defaultdict(list)
    for study in data["studies"]:
        for index, image in enumerate(study["images"]):
            row = source_path_to_index_row.get(image["src"])
            if gps_row(row):
                assert row is not None
                place, transit, explanation = place_from_gps(study["id"], row)
                assignment = {
                    "study_id": study["id"],
                    "src": image["src"],
                    "place": place,
                    "transit": transit,
                    "method": "exact-gps",
                    "evidence": explanation,
                    "raw_city": row.get("city") or "",
                    "gps": {"latitude": float(row["latitude"]), "longitude": float(row["longitude"])},
                    "asset_id_private": row.get("asset_id"),
                    "source_map_asset_id_private": source_ref_by_src.get(image["src"], {}).get("asset_id"),
                    "capture_datetime_exif_indexed": row.get("capture_datetime_exif"),
                    "capture_datetime_asset_indexed": row.get("capture_datetime_asset"),
                    "timezone_indexed": row.get("timezone"),
                }
                study_anchors[study["id"]].append({"image": image, "index": index, "assignment": assignment})
            else:
                assignment = None
            image["_index"] = index
            image["_assignment"] = assignment

    for study in data["studies"]:
        anchors = study_anchors.get(study["id"], [])
        scoped = STUDY_SCOPED_NO_GPS.get(study["id"])
        for image in study["images"]:
            index = image["_index"]
            exact = image.pop("_assignment")
            if exact:
                image["place"] = exact["place"]
                image["transit"] = exact["transit"]
                assignments.append(exact)
            elif anchors:
                anchor, explanation = nearest_anchor(image, study, anchors)
                place = anchor["assignment"]["place"]
                assignment = {
                    "study_id": study["id"],
                    "src": image["src"],
                    "place": place,
                    "transit": False,
                    "method": "nearest-time-no-gps",
                    "evidence": explanation,
                    "anchor_src": anchor["image"]["src"],
                    "anchor_date": anchor["image"].get("d"),
                    "anchor_time": anchor["image"].get("t"),
                    "anchor_asset_id_private": anchor["assignment"].get("asset_id_private"),
                    "source_map_match": bool(source_path_to_index_row.get(image["src"])),
                    "capture_datetime_public": f"{image.get('d', '')} {image.get('t', '')}".strip(),
                    "timezone_public": image.get("tz") or study.get("tz") or "",
                }
                image["place"] = place
                image["transit"] = False
                assignments.append(assignment)
            elif scoped:
                assignment = {
                    "study_id": study["id"],
                    "src": image["src"],
                    "place": scoped["place"],
                    "transit": False,
                    "method": "study-scoped-no-gps",
                    "evidence": scoped["evidence"],
                    "capture_datetime_public": f"{image.get('d', '')} {image.get('t', '')}".strip(),
                }
                image["place"] = scoped["place"]
                image["transit"] = False
                assignments.append(assignment)
            else:
                raise ValueError(f"No GPS anchor or scoped evidence for {study['id']} / {image['src']} (index {index})")
            image.pop("_index")

    # Preserve inherited transit/scout source identity, including the hidden
    # Merritt Island embarkation frame, without moving any numbered routes.
    legacy_transit_sources = {
        image["src"]
        for original in baseline["studies"]
        for series in original["series"] if series.get("displayNumber") == 0
        for image in original["images"][series["start"]:series["start"] + series["count"]]
    }
    for assignment in assignments:
        if assignment["src"] in legacy_transit_sources:
            assignment["transit"] = True
    for study, original in zip(data["studies"], baseline["studies"]):
        for image in study["images"]:
            if image["src"] in legacy_transit_sources:
                image["transit"] = True
        if study["images"][study["key"]]["transit"]:
            study["key"] = next(index for index, image in enumerate(study["images"]) if not image["transit"])
        study["series"] = date_group_series(study, original["series"])
        ordinary_dates = [im.get("d") for im in study["images"] if not im["transit"] and im.get("d")]
        if not original.get("date") and not original.get("dateEnd"):
            # Do not turn inherited album/import timestamps into a known trip date.
            study["date"], study["dateEnd"] = "", ""
        elif ordinary_dates:
            study["date"], study["dateEnd"] = min(ordinary_dates), max(ordinary_dates)

    for study in data["studies"]:
        for image in study["images"]:
            if not image.get("place") or not isinstance(image.get("transit"), bool):
                raise ValueError(f"Incomplete per-image place/transit in {study['id']} / {image['src']}")
            if image["transit"] != (image["se"] == 0):
                raise ValueError(f"Transit and SE mismatch in {study['id']} / {image['src']}")
            if any(key in image for key in ("gps", "lat", "latitude", "lon", "lng", "longitude")):
                raise ValueError(f"GPS data may not be copied into public JSON: {study['id']} / {image['src']}")

    hashes = {
        "source_ref_map_sha256": sha256(source_map_path),
        "archive_index_sha256": sha256(index_path),
        "montreal_supplement_sha256": montreal_delta_hash,
        "public_frozen_baseline_sha256": sha256(baseline_path),
    }
    ledger = {
        "status": "DATA_COMPLETE_PARENT_ACCEPTANCE_PENDING",
        "schema": "outside-place-series-private-assignment-ledger/v1",
        "input_hashes": hashes,
        "total_studies": len(data["studies"]),
        "total_images": sum(len(study["images"]) for study in data["studies"]),
        "exact_gps_assignments": sum(row["method"] == "exact-gps" for row in assignments),
        "nearest_time_assignments": sum(row["method"] == "nearest-time-no-gps" for row in assignments),
        "study_scoped_weak_assignments": sum(row["method"] == "study-scoped-no-gps" for row in assignments),
        "assignments": assignments,
    }
    tables = format_place_series(data["studies"])
    exceptions = format_exceptions(assignments, data["studies"], hashes)
    out_data = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not check:
        private_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(private_dir, 0o700)
        out_path.write_text(out_data)
        (private_dir / "assignment-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")
        (private_dir / "series-table.md").write_text(tables)
        (private_dir / "exceptions.md").write_text(exceptions)
        for path in (private_dir / "assignment-ledger.json", private_dir / "series-table.md", private_dir / "exceptions.md"):
            os.chmod(path, 0o600)
    return {
        "studies": len(data["studies"]),
        "images": ledger["total_images"],
        "exact_gps": ledger["exact_gps_assignments"],
        "nearest_time": ledger["nearest_time_assignments"],
        "study_scoped_weak": ledger["study_scoped_weak_assignments"],
        "series": sum(len(study["series"]) for study in data["studies"]),
        "out_data_sha256": hashlib.sha256(out_data.encode()).hexdigest(),
        "private_dir": str(private_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--source-ref-map", type=Path, default=DEFAULT_SOURCE_MAP)
    parser.add_argument("--archive-index", type=Path, default=DEFAULT_ARCHIVE_INDEX)
    parser.add_argument("--montreal-delta", type=Path, default=DEFAULT_MONTREAL_DELTA)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--private-dir", type=Path, default=DEFAULT_PRIVATE_DIR)
    parser.add_argument("--check", action="store_true", help="Compute and validate without writing.")
    args = parser.parse_args()
    result = migrate(args.data, args.source_ref_map, args.archive_index, args.montreal_delta, args.baseline, args.data, args.private_dir, args.check)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
