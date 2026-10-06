#!/usr/bin/env python3
"""Apply the explicit, GPS-free Outside area mapping and maximal series contract."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "src/data/outside-studies.json"

# Keys are the exact study ids; labels are explicit photo overlay places, not coordinates.
AREA_CONFIG = {
    "new-zealand-2026-july-photos-161007": ({"Auckland": "Auckland", "Waiotapu": "Rotorua", "Rotorua": "Rotorua"}, ["Auckland", "Rotorua"]),
    "australia-2026-july-gallery-20261005-quokka": ({"Bangkok": "Bangkok", "Busselton": "South West", "Dunsborough": "South West", "Yallingup": "South West", "Rottnest Island": "Rottnest Island", "Margaret River": "South West", "Augusta": "South West", "Hamelin Bay": "South West", "Fremantle": "Perth", "Perth": "Perth"}, ["Bangkok", "South West", "Rottnest Island", "Perth"]),
    "pakistan-2026-summer-gallery-20261005": ({"Rome": "Rome", "Tirana": "Tirana", "Karachi": "Karachi", "Murree": "Murree", "Nathia Gali": "Murree", "Islamabad": "Islamabad", "Lahore": "Lahore"}, ["Rome", "Tirana", "Karachi", "Islamabad", "Murree", "Lahore"]),
    "galapagos-2026-january-photos-20261004-20261005-161007": ({"Santa Cruz": "Santa Cruz", "Isabela": "Isabela", "San Cristóbal": "San Cristóbal"}, ["Santa Cruz", "Isabela", "San Cristóbal"]),
    "montreal-november-2025-photos-20261005": ({"Montréal": "Montréal"}, ["Montréal"]),
    "american-southwest-2025-october-gallery-20261004-2-20261005": ({"Joshua Tree": "Joshua Tree", "Las Vegas": "Las Vegas", "Grand Canyon": "Grand Canyon", "Zion": "Zion", "Hoover Dam": "Hoover Dam"}, ["Joshua Tree", "Las Vegas", "Grand Canyon", "Zion", "Hoover Dam"]),
    "georgia-2025-october": ({"Mableton": "Mableton"}, ["Mableton"]),
    "puerto-rico-2025-october": ({"Cataño": "Cataño", "San Juan": "San Juan"}, ["Cataño", "San Juan"]),
    "orlando-2025-september": ({"Orlando": "Orlando"}, ["Orlando"]),
    "sams-point-2025-august": ({"Sam’s Point": "Sam’s Point"}, ["Sam’s Point"]),
    "colorado-2025-july-photos": ({"Boulder": "Boulder", "Denver": "Denver"}, ["Boulder", "Denver"]),
    "puerto-rico-2025-june-photos": ({"Esperanza": "Esperanza"}, ["Esperanza"]),
    "atlanta-2025-june-20261004": ({"Atlanta": "Atlanta"}, ["Atlanta"]),
    "las-vegas-2025-june-gallery-20261004": ({"Las Vegas": "Las Vegas"}, ["Las Vegas"]),
    "colorado-2025-june-gallery": ({"Green Mountain Falls": "Green Mountain Falls", "Manitou Springs": "Manitou Springs", "Denver": "Denver", "Glenwood Springs": "Glenwood Springs", "Estes Park": "Estes Park"}, ["Green Mountain Falls", "Manitou Springs", "Denver", "Glenwood Springs", "Estes Park"]),
    "cruise-2024-december-gallery": ({"Merritt Island": "Merritt Island", "Eatontown": "Eatontown", "Manahawkin": "Manahawkin", "Nassau": "Nassau"}, ["Merritt Island", "Eatontown", "Manahawkin", "Nassau"]),
    "maryland-national-harbor-2023-august": ({"National Harbor": "National Harbor"}, ["National Harbor"]),
    "montreal-august-2023-photos": ({"Montréal": "Montréal"}, ["Montréal"]),
    "philadelphia-2023-spring-gallery": ({"Philadelphia": "Philadelphia"}, ["Philadelphia"]),
    "point-lookout-2015-august": ({"Point Lookout": "Point Lookout"}, ["Point Lookout"]),
    "europe-shared-album": ({"Location unconfirmed": "Location unconfirmed"}, ["Location unconfirmed"]),
}
PLACE_RENAMES = {"pakistan-2026-summer-gallery-20261005": {"Albania": "Tirana"}}


def make_series(study: dict) -> list[dict]:
    images = study["images"]
    transit_count = sum(bool(image.get("transit")) for image in images)
    if any(image.get("transit") for image in images[transit_count:]):
        raise ValueError(f"transit images must remain a source-order prefix: {study['id']}")

    series = []
    prior_titles = {}
    for previous in study.get("series", []):
        for index in range(previous["start"], previous["start"] + previous["count"]):
            prior_titles[index] = previous.get("title", "")
    if transit_count:
        transit_images = images[:transit_count]
        dates = [image.get("d", "") for image in transit_images if image.get("d")]
        places = list(dict.fromkeys(image["place"] for image in transit_images))
        for image in transit_images:
            image["se"] = 0
        series.append({
            "start": 0,
            "count": transit_count,
            "time": transit_images[0].get("t", ""),
            "key": 0,
            "displayNumber": 0,
            "date": min(dates) if dates else "",
            "dateEnd": max(dates) if dates else "",
            "title": "SCOUT · " + ", ".join(places),
        })

    cursor = transit_count
    next_number = 1
    while cursor < len(images):
        image = images[cursor]
        group = (image.get("d", ""), image["area"])
        end = cursor + 1
        while end < len(images) and not images[end].get("transit") and (images[end].get("d", ""), images[end]["area"]) == group:
            end += 1
        run = images[cursor:end]
        prior_keys = [row.get("key", row["start"]) for row in study.get("series", [])
                      if cursor <= row.get("key", row["start"]) < end]
        for image_in_run in run:
            image_in_run["se"] = next_number
        series.append({
            "start": cursor,
            "count": len(run),
            "time": image.get("t", ""),
            "key": prior_keys[0] if prior_keys else cursor,
            "displayNumber": next_number,
            "date": image.get("d", ""),
            "dateEnd": run[-1].get("d", ""),
            "title": prior_titles.get(cursor) or image["area"],
        })
        next_number += 1
        cursor = end
    return series


def migrate(data: dict) -> dict:
    result = copy.deepcopy(data)
    studies = {study["id"]: study for study in result["studies"]}
    if set(studies) != set(AREA_CONFIG):
        missing = sorted(set(studies) - set(AREA_CONFIG))
        absent = sorted(set(AREA_CONFIG) - set(studies))
        raise ValueError(f"study map mismatch; unmapped={missing}, absent={absent}")

    for study_id, (area_map, area_order) in AREA_CONFIG.items():
        study = studies[study_id]
        renames = PLACE_RENAMES.get(study_id, {})
        for image in study["images"]:
            image["place"] = renames.get(image["place"], image["place"])
        places = {image["place"] for image in study["images"]}
        if not places <= set(area_map):
            raise ValueError(f"explicit place map mismatch for {study_id}: places={sorted(places)}, map={sorted(area_map)}")
        study["areaMap"] = area_map
        study["areaOrder"] = area_order
        for image in study["images"]:
            image["area"] = area_map[image["place"]]
        study["series"] = make_series(study)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the data file differs from the migration output")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="data JSON path (defaults to the repository data file)")
    args = parser.parse_args()
    raw = args.data.read_text(encoding="utf-8")
    current = json.loads(raw)
    rendered = json.dumps(migrate(current), ensure_ascii=False, indent=2) + "\n"
    if raw == rendered:
        print("Outside area data is current.")
        return 0
    if args.check:
        print("Outside area data drift detected; run scripts/migrate_outside_area_series.py.", file=sys.stderr)
        return 1
    args.data.write_text(rendered, encoding="utf-8")
    print("Migrated Outside area mappings and date/area series.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
