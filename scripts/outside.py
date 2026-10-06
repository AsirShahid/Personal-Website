#!/usr/bin/env python3
"""Outside Studies content edits.

  python scripts/outside.py remove TARGET...
      Remove photos. Each TARGET is a photo link (https://asir.dev/outside/#study/p1a2b3c4d, or an old
      #study/12 link), a photo id, a /outside/... source, or an outside-photo-review/v1 export file.
      Safe to re-run.

  python scripts/outside.py add --study STUDY_ID --file ORIGINAL.jpg --src /outside/assets/DIR/NAME [--alt TEXT] [--place PLACE]
      Add one photo: writes the -s/-m/-l WebP derivatives (sRGB, metadata stripped), reads capture
      metadata from EXIF, and inserts the record chronologically.

  python scripts/outside.py check
      Exit non-zero if stored series/covers differ from what the rebuild would produce.

Photos carry stable ids, and old numbered links live in the frozen src/data/outside-legacy-links.json,
so edits never renumber or rewrite links: a removed photo's links simply become unavailable.
Removed sources are recorded in src/data/outside-removed-sources.json so they are never re-added by accident.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/data/outside-studies.json"
REMOVED = ROOT / "src/data/outside-removed-sources.json"
LEGACY = ROOT / "src/data/outside-legacy-links.json"
PUBLIC = ROOT / "public"
SIZES = {"s": (360, 70), "m": (1080, 78), "l": (1920, 80)}


def photo_id(src: str) -> str:
    return "p" + hashlib.sha1(src.encode()).hexdigest()[:8]


def first_se1_index(study: dict) -> int:
    images = study["images"]
    k = next((i for i, image in enumerate(images) if image.get("se") == 1), None)
    if k is None:
        k = next((i for i, image in enumerate(images) if not image.get("transit")), 0)
    return k


def resolve(data: dict, legacy: dict, link: str) -> str | None:
    """Return the photo src a link opens, or None if the page would say it is unavailable.

    Python mirror of parseHash() in src/pages/outside.astro; tests check the two agree.
    """
    match = re.fullmatch(r"([\w-]+)(?:/([\w-]+))?", link.split("#", 1)[-1])
    if not match:
        return None
    route_id, part = match.groups()
    studies = {study["id"]: study for study in data["studies"]}
    by_id = {image["id"]: image["src"] for study in data["studies"] for image in study["images"]}
    if part and not re.fullmatch(r"[1-9]\d*", part):
        return by_id.get(part)
    old = legacy.get(route_id)
    if old is not None:
        if part is None:
            study = studies.get(old["study"]) if old["study"] else None
            return study["images"][first_se1_index(study)]["src"] if study else None
        k = int(part) - 1
        if k >= len(old["photos"]):
            if not old.get("clamp") or not old["photos"]:
                return None
            k = len(old["photos"]) - 1
        return by_id.get(old["photos"][k]) if old["photos"][k] else None
    study = studies.get(route_id)
    if study is None:
        return None
    if part is None:
        return study["images"][first_se1_index(study)]["src"]
    return study["images"][min(int(part) - 1, len(study["images"]) - 1)]["src"]


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rebuild(study: dict, old: dict | None = None) -> None:
    """Recompute series from consecutive (date, area) runs; keep titles, series covers and the study cover by photo id."""
    old = old or study
    old_images = old["images"]
    title_of, series_keys = {}, set()
    for row in old["series"]:
        for image in old_images[row["start"]:row["start"] + row["count"]]:
            title_of.setdefault(image["id"], row.get("title", ""))
        if 0 <= row.get("key", row["start"]) < len(old_images):
            series_keys.add(old_images[row.get("key", row["start"])]["id"])
    cover_id = old_images[old["key"]]["id"] if 0 <= old.get("key", 0) < len(old_images) else None

    images = study["images"]
    transit = sum(bool(image.get("transit")) for image in images)
    if any(image.get("transit") for image in images[transit:]):
        raise ValueError(f"transit photos must stay a prefix: {study['id']}")
    series = []
    if transit:
        run = images[:transit]
        dates = [image["d"] for image in run if image.get("d")]
        for image in run:
            image["se"] = 0
        series.append({"start": 0, "count": transit, "time": run[0].get("t", ""), "key": 0, "displayNumber": 0,
                       "date": min(dates) if dates else "", "dateEnd": max(dates) if dates else "",
                       "title": "SCOUT · " + ", ".join(dict.fromkeys(image["place"] for image in run))})
    cursor, number = transit, 1
    while cursor < len(images):
        group = (images[cursor].get("d", ""), images[cursor]["area"])
        end = cursor + 1
        while end < len(images) and (images[end].get("d", ""), images[end]["area"]) == group:
            end += 1
        run = images[cursor:end]
        for image in run:
            image["se"] = number
        titles = [title_of[image["id"]] for image in run if title_of.get(image["id"])]
        keys = [cursor + k for k, image in enumerate(run) if image["id"] in series_keys]
        series.append({"start": cursor, "count": len(run), "time": run[0].get("t", ""), "key": keys[0] if keys else cursor,
                       "displayNumber": number, "date": run[0].get("d", ""), "dateEnd": run[-1].get("d", ""),
                       "title": titles[0] if titles else run[0]["area"]})
        number += 1
        cursor = end
    study["series"] = series
    ids = [image["id"] for image in images]
    ordinary = [k for k, image in enumerate(images) if not image.get("transit")]
    study["key"] = ids.index(cover_id) if cover_id in ids else (ordinary[0] if ordinary else 0)
    old_dates = sorted(image["d"] for image in old_images if image.get("d") and not image.get("transit"))
    new_dates = sorted(image["d"] for image in images if image.get("d") and not image.get("transit"))
    if old_dates and new_dates and (old.get("date"), old.get("dateEnd")) == (old_dates[0], old_dates[-1]):
        study["date"], study["dateEnd"] = new_dates[0], new_dates[-1]


def targets_to_sources(data: dict, targets: list[str]) -> list[str]:
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    by_id = {image["id"]: image["src"] for study in data["studies"] for image in study["images"]}
    # Ids of photos removed earlier still name them, so repeating a removal is a no-op, not an error.
    removed = json.loads(REMOVED.read_text(encoding="utf-8")) if REMOVED.exists() else []
    by_id.update({photo_id(src): src for src in removed if photo_id(src) not in by_id})
    sources = []
    for target in targets:
        if target.endswith(".json") and Path(target).is_file():
            export = json.loads(Path(target).read_text(encoding="utf-8"))
            if export.get("schema") != "outside-photo-review/v1":
                sys.exit(f"unexpected export schema in {target}: {export.get('schema')!r}")
            sources += [row["src"] for row in export.get("flagged", [])]
        elif target.startswith("/outside/"):
            sources.append(target)
        elif re.fullmatch(r"p[0-9a-f]{8}", target):
            if target not in by_id:
                sys.exit(f"no photo has id {target}")
            sources.append(by_id[target])
        else:
            if "/" not in target.split("#", 1)[-1]:
                sys.exit(f"{target} opens a whole study, not one photo; copy the link while that photo is open")
            part = target.split("#", 1)[-1].split("/", 1)[1]
            src = by_id.get(part) if re.fullmatch(r"p[0-9a-f]{8}", part) else resolve(data, legacy, target)
            if src is None:
                sys.exit(f"{target} does not open a photo")
            sources.append(src)
    return list(dict.fromkeys(sources))


def cmd_remove(args) -> int:
    data = load()
    flagged = targets_to_sources(data, args.targets)
    present = {image["src"] for study in data["studies"] for image in study["images"]}
    removing = [src for src in flagged if src in present]
    emptied = []
    for study in data["studies"]:
        kept = [image for image in study["images"] if image["src"] not in removing]
        if len(kept) == len(study["images"]):
            continue
        if not kept:
            emptied.append(study["id"])
            continue
        old = json.loads(json.dumps(study))
        study["images"] = kept
        rebuild(study, old)
    data["studies"] = [study for study in data["studies"] if study["id"] not in emptied]
    save(data)
    removed = set(json.loads(REMOVED.read_text(encoding="utf-8"))) if REMOVED.exists() else set()
    REMOVED.write_text(json.dumps(sorted(removed | set(removing)), indent=1) + "\n", encoding="utf-8")
    print(f"flagged {len(flagged)}: removed {len(removing)}, already absent {len(flagged) - len(removing)}")
    for src in removing:
        print("  removed", src)
    for study_id in emptied:
        print("  removed now-empty study", study_id)
    return 0


def exif_record(path: Path) -> tuple[dict, object]:
    from PIL import Image, ImageOps
    try:
        import pillow_heif  # optional HEIC support
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    image = Image.open(path)
    exif = image.getexif()
    sub = exif.get_ifd(0x8769)
    image = ImageOps.exif_transpose(image)
    stamp = str(sub.get(36867) or exif.get(306) or "")
    d, t = (stamp[:10].replace(":", "-"), stamp[11:19]) if len(stamp) >= 19 else ("", "")
    offset = str(sub.get(36881) or "")
    parts = []
    if sub.get(34855):
        parts.append(f"ISO {int(sub[34855])}")
    if sub.get(33434):
        exposure = float(sub[33434])
        parts.append(f"1/{round(1 / exposure)} s" if exposure < 1 else f"{Fraction(exposure).limit_denominator(10)} s")
    if sub.get(33437):
        parts.append(f"f/{float(sub[33437]):g}")
    camera = " ".join(str(exif.get(tag) or "").strip() for tag in (271, 272)).strip()
    record = {"w": image.width, "h": image.height, "d": d, "t": t, "ex": "  ".join(parts),
              "fl": f"{round(float(sub[37386]), 2):g} mm" if sub.get(37386) else "", "cam": camera, "avg": "",
              "tz": f"UTC{offset}" if offset else ""}
    return record, image


def write_derivatives(image, src: str) -> None:
    from PIL import Image, ImageCms
    icc = image.info.get("icc_profile")
    image = image.convert("RGB")
    srgb = ImageCms.createProfile("sRGB")
    if icc:
        image = ImageCms.profileToProfile(image, ImageCms.ImageCmsProfile(io.BytesIO(icc)), srgb, outputMode="RGB")
    srgb_bytes = ImageCms.ImageCmsProfile(srgb).tobytes()
    target = PUBLIC / src.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    for suffix, (edge, quality) in SIZES.items():
        copy = image.copy()
        copy.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        copy.save(f"{target}-{suffix}.webp", "WEBP", quality=quality, method=5, icc_profile=srgb_bytes)


def cmd_add(args) -> int:
    data = load()
    study = next((row for row in data["studies"] if row["id"] == args.study), None)
    if study is None:
        sys.exit(f"unknown study: {args.study}")
    if not args.src.startswith("/outside/") or any(image["src"] == args.src for row in data["studies"] for image in row["images"]):
        sys.exit(f"source must be a new /outside/... path: {args.src}")
    if REMOVED.exists() and args.src in json.loads(REMOVED.read_text(encoding="utf-8")) and not args.allow_removed:
        sys.exit(f"{args.src} was removed earlier; pass --allow-removed to restore it on purpose")
    record, image = exif_record(Path(args.file))
    place = args.place or next((row["place"] for row in study["images"] if row.get("d") == record["d"] and not row.get("transit")), "")
    if place not in study.get("areaMap", {}):
        sys.exit(f"pass --place; known places: {sorted(study.get('areaMap', {}))}")
    entry = {"id": photo_id(args.src), "src": args.src, **record, "se": 1, "place": place,
             "transit": False, "area": study["areaMap"][place]}
    if args.alt:
        entry["alt"] = args.alt
    write_derivatives(image, args.src)
    old = json.loads(json.dumps(study))
    stamp = (entry["d"], entry["t"])
    position = next((k for k, row in enumerate(study["images"])
                     if not row.get("transit") and (row.get("d", ""), row.get("t", "")) > stamp), len(study["images"]))
    study["images"].insert(position, entry)
    rebuild(study, old)
    save(data)
    print(f"added {args.src} as {entry['id']} to {study['id']} at photo {position + 1}")
    print(f"link: https://asir.dev/outside/#{study['id']}/{entry['id']}")
    return 0


def cmd_check(_args) -> int:
    data = load()
    drift = []
    for study in data["studies"]:
        rebuilt = json.loads(json.dumps(study))
        rebuild(rebuilt)
        if rebuilt != study:
            drift.append(study["id"])
    if drift:
        print("series/cover drift:", ", ".join(drift), file=sys.stderr)
        return 1
    print("Outside data is consistent.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    remove = sub.add_parser("remove")
    remove.add_argument("targets", nargs="+")
    add = sub.add_parser("add")
    add.add_argument("--study", required=True)
    add.add_argument("--file", required=True)
    add.add_argument("--src", required=True)
    add.add_argument("--alt")
    add.add_argument("--place")
    add.add_argument("--allow-removed", action="store_true")
    sub.add_parser("check")
    args = parser.parse_args()
    return {"remove": cmd_remove, "add": cmd_add, "check": cmd_check}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
