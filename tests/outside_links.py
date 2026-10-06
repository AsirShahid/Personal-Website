"""Outside test helpers: the script's link resolver bound to the current data."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
_spec = importlib.util.spec_from_file_location("outside_script", ROOT / "scripts/outside.py")
_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_script)

DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
LEGACY = json.loads((ROOT / "src/data/outside-legacy-links.json").read_text())
photo_id = _script.photo_id
first_se1_index = _script.first_se1_index


def resolve(link):
    """Return the photo src a link opens, or None when the page shows "no longer available"."""
    return _script.resolve(DATA, LEGACY, link)
