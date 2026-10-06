import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[1]
DATA = ROOT / "src/data/outside-studies.json"
PUBLIC = ROOT / "public"
SOURCE = "/outside/assets/owner-review/summer-2026/S0659"
AUSTRALIA_ID = "australia-2026-july-gallery-20261005-quokka"
OLD_AUSTRALIA_ID = "australia-2026-july-gallery-20261005-161007"
BASELINE_IMAGE_RECORDS_SHA256 = "e5cb42dabbde26269ca6fc35a665b517db7dd7fc8b6d8e25f881149e3ed8e40c"
BASELINE_ALIAS_SOURCE_MAP_SHA256 = "26ea08ce84dd81be1c7195e366ac0ccfc8a54d7a11b00217e72969f8d216becc"
BASELINE_OPENINGS_SHA256 = "06522840b7461e87773660f44b841c02c89869b285ab2cf148d79d429c2c2045"


def canonical_hash(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def image_source(data, target):
    if not isinstance(target, dict):
        return None
    study = next((row for row in data["studies"] if row["id"] == target.get("studyId")), None)
    index = target.get("index")
    if study is None or not isinstance(index, int) or isinstance(index, bool):
        return None
    return study["images"][index]["src"] if 0 <= index < len(study["images"]) else None


def resolved_alias_sources(data):
    result = {}
    for name, alias in sorted(data["aliases"].items()):
        if isinstance(alias.get("targets"), list):
            targets = [image_source(data, target) for target in alias["targets"]]
            if "defaultTarget" in alias:
                default_target = alias["defaultTarget"]
            else:
                default_target = next((target for target in alias["targets"] if image_source(data, target)), None)
            result[name] = {"targets": targets, "default": image_source(data, default_target)}
        else:
            indices = alias.get("indices", [])
            targets = [image_source(data, {"studyId": alias.get("studyId"), "index": index}) for index in indices]
            default_index = alias.get("defaultIndex")
            if default_index is None:
                default_index = next((index for index in indices if isinstance(index, int) and not isinstance(index, bool) and index >= 0), None)
            result[name] = {
                "targets": targets,
                "default": image_source(data, {"studyId": alias.get("studyId"), "index": default_index}),
            }
    return result


def existing_openings(data):
    openings = {}
    for study in data["studies"]:
        key = study.get("key", 0)
        openings[study["id"]] = {
            "study_cover": study["images"][key]["src"],
            "first_se1": next((image["src"] for image in study["images"] if image.get("se") == 1), None),
            "series_openings": [(series["displayNumber"], study["images"][series["key"]]["src"]) for series in study["series"]],
        }
    return openings


def test_owner_selected_bicycle_quokka_is_the_only_source_safe_addition():
    data = json.loads(DATA.read_text())
    studies = {study["id"]: study for study in data["studies"]}
    all_images = [image for study in data["studies"] for image in study["images"]]
    matches = [image for image in all_images if image["src"] == SOURCE]

    assert len(data["studies"]) == 21
    assert len(all_images) == 414
    assert len(matches) == 1
    assert data["aliases"] and len(data["aliases"]) == 132
    image = matches[0]
    assert image == {
        "src": SOURCE,
        "w": 2352,
        "h": 3136,
        "d": "2026-07-11",
        "t": "11:30:03",
        "se": 4,
        "ex": "ISO 50  1/216 s  f/2",
        "fl": "7.1 mm",
        "cam": "OnePlus OnePlus 11 5G",
        "avg": "",
        "tz": "UTC+08:00",
        "place": "Rottnest Island",
        "area": "Rottnest Island",
        "transit": False,
        "alt": "A quokka beside a bicycle on a paved path at Rottnest Island.",
    }
    assert not ({"lat", "lon", "gps", "GPS", "archive_id"} & image.keys())

    # Complete immutable metadata/source preservation is pinned independently
    # in test_outside_area_data against the pre-migration current-main fixture.
    prior_images = [row for row in all_images if row["src"] != SOURCE]
    assert len(prior_images) == 413
    alias_sources = resolved_alias_sources(data)
    alias_sources.pop(OLD_AUSTRALIA_ID)
    assert canonical_hash(alias_sources) == BASELINE_ALIAS_SOURCE_MAP_SHA256
    baseline = json.loads((ROOT / "tests/fixtures/outside-area-source-baseline.json").read_text())
    openings = existing_openings(data)
    for snap in baseline["studies"]:
        assert openings[snap["id"]]["study_cover"] == snap["cover_src"]
        assert openings[snap["id"]]["first_se1"] == snap["first_se1_src"]

    australia = studies[AUSTRALIA_ID]
    selected_index = australia["images"].index(image)
    assert selected_index == 14
    assert [australia["images"][i]["src"] for i in range(15, 18)] == [
        "/outside/assets/owner-review/summer-2026/S0690",
        "/outside/assets/owner-review/summer-2026/S0720",
        "/outside/assets/owner-review/summer-2026/S0762",
    ]
    rot_series = next(series for series in australia["series"] if series["displayNumber"] == 4)
    assert (rot_series["start"], rot_series["count"], rot_series["time"], rot_series["key"]) == (14, 4, "11:30:03", 15)

    for size, expected_dimensions in {"s": (270, 360), "m": (810, 1080), "l": (1440, 1920)}.items():
        path = PUBLIC / f"{SOURCE.lstrip('/')}\u002d{size}.webp"
        with Image.open(path) as derivative:
            derivative.load()
            assert derivative.format == "WEBP"
            assert derivative.size == expected_dimensions
            assert not derivative.getexif()
            assert "xmp" not in derivative.info
