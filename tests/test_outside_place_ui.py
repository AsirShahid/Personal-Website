import copy
import json
import os
import re
import subprocess
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parents[1]
DATA = json.loads((ROOT / "src/data/outside-studies.json").read_text())
HELPER_URL = (ROOT / "src/utils/outside-place.js").as_uri()
BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/outside/")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def is_transit(image):
    return image.get("transit") is True or image.get("se") == 0


def unique(values):
    return list(dict.fromkeys(value for value in values if isinstance(value, str) and value.strip()))


def location_line(study):
    images = study["images"]
    ordinary_areas = {image.get("area") for image in images if not is_transit(image)}
    transit_areas = {image.get("area") for image in images if is_transit(image)}
    present = unique(image.get("area") for image in images)
    configured = study.get("areaOrder", [])
    area_order = [area for area in configured if area in present] + [area for area in present if area not in configured]
    areas = [area for area in area_order if area in ordinary_areas]
    travel_areas = [area for area in area_order if area in transit_areas]
    if len(areas) == 1 and areas[0] == study["place"] and study.get("country"):
        areas = [study["country"]]
    line = " · ".join(areas) if areas else "Location unconfirmed"
    if travel_areas:
        line += " · via " + ", ".join(travel_areas)
    return line


def compact_date(start, end):
    if not start:
        return end or ""
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(end) if end else first
    except (TypeError, ValueError):
        return start if not end or end == start else f"{start} to {end}"
    fmt = lambda value: f"{MONTHS[value.month - 1]} {value.day}"
    if first == last:
        return f"{fmt(first)}, {first.year}"
    if first.year == last.year and first.month == last.month:
        return f"{MONTHS[first.month - 1]} {first.day}–{last.day}, {first.year}"
    if first.year == last.year:
        return f"{fmt(first)} – {fmt(last)}, {first.year}"
    return f"{fmt(first)}, {first.year} – {fmt(last)}, {last.year}"


def strip_date(value):
    if not value:
        return ""
    parsed = date.fromisoformat(value)
    return f"{MONTHS[parsed.month - 1]} {parsed.day}"


def make_transit_fixture():
    payload = copy.deepcopy(DATA)
    for study in payload["studies"]:
        for image in study["images"]:
            image["place"] = study["place"]
            image["area"] = study["place"]
            image["transit"] = False
            image["se"] = 1
        study["areaOrder"] = [study["place"]]
    excluded = {"puerto-rico-2025-june-photos", "puerto-rico-2025-october", "georgia-2025-october"}
    include = {"puerto-rico-2025-june-photos"}
    ordered = sorted(payload["studies"], key=lambda study: (study.get("dateEnd") or study.get("date") or "", study.get("date") or ""), reverse=True)
    payload["recentStudyIds"] = [
        study["id"] for study in ordered
        if study["id"] not in excluded and (study["id"] in include or (study.get("date", "") and study["date"] >= "2025-10-01"))
    ]
    recent = payload["recentStudyIds"][0]
    study = next(item for item in payload["studies"] if item["id"] == recent)
    if len(study["images"]) < 3:
        raise AssertionError("transit browser fixture needs three retained images")
    study["images"][0].update(place="Rome", area="Rome", transit=True, se=0)
    study["images"][1].update(place="Tirana", area="Tirana", transit=True, se=0)
    study["images"][2].update(place=study["place"], area=study["place"], transit=False, se=1)
    study["areaOrder"] = [study["place"]]
    study["series"] = [
        {"start": 0, "count": 2, "time": "Rome · Tirana", "date": study["date"], "dateEnd": study["dateEnd"], "key": 0, "displayNumber": 0},
        {"start": 2, "count": len(study["images"]) - 2, "time": "Main visit", "date": study["date"], "dateEnd": study["dateEnd"], "key": 2, "displayNumber": 1},
    ]
    study["key"] = 2
    payload.setdefault("aliases", {})["place-series-alias-regression"] = {
        "targets": [{"studyId": study["id"], "index": index} for index in range(len(study["images"]))],
        "defaultTarget": {"studyId": study["id"], "index": 0},
    }
    return payload, study["id"]


class OutsidePlaceUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        browser_name = os.environ.get("OUTSIDE_BROWSER", "chromium")
        cls.browser = getattr(cls.playwright, browser_name).launch(headless=True)
        cls.studies = {study["id"]: study for study in DATA["studies"]}

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_area_helpers_use_explicit_area_order_country_and_skip_scouts(self):
        script = f'''try {{
  const h = await import({json.dumps(HELPER_URL)});
  const study = {{place:"Montréal", region:"Québec", country:"Canada", key:0, areaOrder:["Montréal"], images:[
    {{src:"/transit", place:"Rome", area:"Rome", se:0, transit:true}},
    {{src:"/transit2", place:"Tirana", area:"Tirana", se:0, transit:true}},
    {{src:"/transit3", place:"Rome", area:"Rome", se:0, transit:true}},
    {{src:"/ordinary", place:"Montréal", area:"Montréal", se:1, transit:false}}
  ]}};
  const multi = {{place:"Somewhere", region:"Fallback region", country:"", areaOrder:["Lisbon","Paris"], images:[
    {{place:"Paris", area:"Paris", se:1}}, {{place:"Lisbon", area:"Lisbon", se:2}}, {{place:"Paris", area:"Paris", se:3}}, {{place:"Zurich", area:"Zurich", se:0}}
  ]}};
  const empty = {{place:"Unknown", region:"Must not appear", country:"", areaOrder:[], images:[{{se:1}}]}};
  console.log(JSON.stringify({{available: typeof h.getOutsideStudyAreaSummary === "function" && typeof h.getOutsideStudyCover === "function" && typeof h.getOutsideFirstImageIndex === "function", country:h.getOutsideStudyAreaSummary?.(study), multi:h.getOutsideStudyAreaSummary?.(multi), empty:h.getOutsideStudyAreaSummary?.(empty), cover:h.getOutsideStudyCover?.(study)?.src, first:h.getOutsideFirstImageIndex?.(study)}}));
}} catch (error) {{ console.log(JSON.stringify({{available:false, error:String(error)}})); }}'''
        result = subprocess.run(["node", "--input-type=module", "-e", script], check=True, capture_output=True, text=True)
        observed = json.loads(result.stdout)
        self.assertTrue(observed["available"], observed)
        self.assertEqual(observed["country"], "Canada · via Rome, Tirana")
        self.assertEqual(observed["multi"], "Lisbon · Paris · via Zurich")
        self.assertEqual(observed["empty"], "")  # Never invent a label or fall back to study-level place.
        self.assertEqual(observed["cover"], "/ordinary")
        self.assertEqual(observed["first"], 3)

    def open_page(self, fragment="", width=1440, transit_fixture=False, fixture_payload=None):
        context = self.browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.route("**/*.webp", lambda route: route.abort())
        if transit_fixture:
            payload = fixture_payload if fixture_payload is not None else make_transit_fixture()[0]

            def fixture_response(route):
                response = route.fetch()
                html = response.text()
                encoded = json.dumps(payload, ensure_ascii=False)
                html, replaced = re.subn(
                    r'(<script type="application/json" id="oz-data"[^>]*>).*?(</script>)',
                    lambda match: match.group(1) + encoded + match.group(2),
                    html,
                    count=1,
                    flags=re.DOTALL,
                )
                if replaced != 1:
                    route.abort()
                    return
                route.fulfill(response=response, body=html)

            page.route("**/outside/", fixture_response)
        page.goto(urljoin(BASE_URL, fragment), wait_until="domcontentloaded")
        page.wait_for_function("document.body.classList.contains('is-ready')", timeout=15000)
        return context, page

    @staticmethod
    def current_source(page):
        return page.locator("[data-cells] img").first.get_attribute("data-want") or ""

    @staticmethod
    def index_for_se(study, se_number):
        return next(index for index, image in enumerate(study["images"]) if image.get("se") == se_number)

    def test_worklist_keeps_three_content_lines_visible_on_desktop_and_phone(self):
        for width in (1440, 375):
            with self.subTest(width=width):
                context, page = self.open_page(width=width)
                payload = json.loads(page.locator("#oz-data").text_content() or "{}")
                visible_ids = payload["recentStudyIds"]
                self.assertEqual(page.locator(".oz-row").count(), len(visible_ids))
                for study_id in visible_ids:
                    study = self.studies[study_id]
                    row = page.locator(f'.oz-row[href="#{study_id}"]')
                    row_text = row.locator(".oz-rowtext")
                    self.assertTrue(row_text.is_visible(), study_id)
                    self.assertEqual(row_text.locator(":scope > .oz-place").inner_text(), study["place"])
                    expected_date = compact_date(study.get("date", ""), study.get("dateEnd", ""))
                    self.assertEqual(row_text.locator(":scope > .oz-row-dates > .oz-row-date").inner_text(), expected_date)
                    self.assertEqual(row_text.locator(":scope > .oz-row-dates > .oz-row-count").inner_text(), f"{len(study['images'])} IM")
                    self.assertEqual(row_text.locator(":scope > .oz-region").inner_text(), location_line(study))
                    self.assertEqual(row_text.locator(":scope > .oz-region").evaluate("el => getComputedStyle(el).webkitLineClamp"), "2")
                    cover_index = study.get("key", 0)
                    preferred = study["images"][cover_index] if isinstance(cover_index, int) and 0 <= cover_index < len(study["images"]) else None
                    non_transit = preferred if preferred and not is_transit(preferred) else next((image for image in study["images"] if not is_transit(image)), None)
                    thumb = row.locator(".oz-thumb img").get_attribute("src") or ""
                    if non_transit:
                        self.assertTrue(thumb.startswith(non_transit["src"] + "-s.webp"), study_id)
                        self.assertFalse(is_transit(non_transit))
                    else:
                        self.assertNotIn("-se0", thumb, study_id)
                context.close()

    def test_compact_worklist_date_and_count_stay_fully_visible_at_required_widths(self):
        for width in (1440, 375):
            with self.subTest(width=width):
                context, page = self.open_page(width=width)
                row = page.locator(".oz-row").first
                date_span = row.locator(".oz-row-date")
                count_span = row.locator(".oz-row-count")
                date_span.evaluate("el => el.textContent = 'Jun 28 – Jul 5, 2026'")
                count_span.evaluate("el => el.textContent = '413 IM'")
                dimensions = page.evaluate("""row => {
                  const date = row.querySelector('.oz-row-date');
                  const count = row.querySelector('.oz-row-count');
                  return {dateClient:date.clientWidth, dateScroll:date.scrollWidth, countClient:count.clientWidth, countScroll:count.scrollWidth};
                }""", row.element_handle())
                self.assertLessEqual(dimensions["dateScroll"], dimensions["dateClient"], dimensions)
                self.assertLessEqual(dimensions["countScroll"], dimensions["countClient"], dimensions)
                context.close()

    def test_mobile_worklist_cards_do_not_duplicate_or_overlap_metadata(self):
        context, page = self.open_page(width=375)
        row = page.locator(".oz-row").first
        self.assertEqual(row.locator(".oz-card-tl").evaluate("el => getComputedStyle(el).display"), "none")
        self.assertEqual(row.locator(".oz-card-bl").evaluate("el => getComputedStyle(el).display"), "none")
        self.assertTrue(page.evaluate("""row => {
          const tr = row.querySelector('.oz-card-tr').getBoundingClientRect();
          const br = row.querySelector('.oz-card-br').getBoundingClientRect();
          return tr.bottom <= br.top || br.bottom <= tr.top || tr.right <= br.left || br.right <= tr.left;
        }""", row.element_handle()))
        context.close()

    def test_plain_canonical_and_alias_hashes_use_se1_but_numbered_alias_keeps_target(self):
        fixture_payload, study_id = make_transit_fixture()
        study = next(item for item in fixture_payload["studies"] if item["id"] == study_id)
        first_se1 = self.index_for_se(study, 1)
        context, page = self.open_page(f"#{study_id}", transit_fixture=True)
        self.assertTrue(self.current_source(page).startswith(study["images"][first_se1]["src"]))
        context.close()

        context, page = self.open_page("#place-series-alias-regression", transit_fixture=True)
        self.assertTrue(self.current_source(page).startswith(study["images"][first_se1]["src"]))
        context.close()

        context, page = self.open_page("#place-series-alias-regression/1", transit_fixture=True)
        self.assertTrue(self.current_source(page).startswith(study["images"][0]["src"]))
        context.close()

    def test_series_area_never_substitutes_for_missing_image_area(self):
        fixture_payload, study_id = make_transit_fixture()
        study = next(item for item in fixture_payload["studies"] if item["id"] == study_id)
        study["series"][1]["title"] = "Not an area"
        for image in study["images"][2:]:
            image["area"] = ""
        context, page = self.open_page(f"#{study_id}/3", transit_fixture=True, fixture_payload=fixture_payload)
        label = page.locator('[data-series] [data-se="1"] .oz-se-cap > span').inner_text()
        self.assertEqual(label, "")
        self.assertNotIn("Not an area", page.locator('[data-series] [data-se="1"] .oz-se-cap').inner_text())
        context.close()

    def test_transit_overlay_scout_strip_and_open_navigation_defaults(self):
        fixture_payload, study_id = make_transit_fixture()
        study = next(item for item in fixture_payload["studies"] if item["id"] == study_id)
        transit_index = next(index for index, image in enumerate(study["images"]) if is_transit(image))
        transit = study["images"][transit_index]
        transit_series_index = next(index for index, series in enumerate(study["series"]) if series.get("displayNumber") == 0)
        transit_series = study["series"][transit_series_index]
        first_se1 = self.index_for_se(study, 1)

        # Explicit ordinal routes keep their historical one-based image mapping, including SE 0.
        context, page = self.open_page(f"#{study['id']}/{transit_index + 1}", transit_fixture=True)
        self.assertTrue(self.current_source(page).startswith(transit["src"]))
        tl = page.locator('[data-ov="tl"]').inner_text().splitlines()
        self.assertEqual(tl[0], study["place"].upper())
        self.assertEqual(tl[1], f"{transit['place']} · TRANSIT".upper())
        self.assertNotIn(study.get("region", "").upper(), tl[1])
        self.assertIn("STUDY ", tl[2])
        self.assertIn("XC · ", tl[3])
        scout = page.locator('[data-ov="br"] .oz-ov-status.oz-st-prelim').get_by_text("SCOUT", exact=True)
        self.assertEqual(scout.inner_text(), "SCOUT")
        self.assertEqual(page.locator('[data-ov="br"] .oz-ov-status').all_inner_texts(), ["SCOUT"])

        strip = page.locator(f'[data-series] [data-se="{transit_series_index}"]')
        self.assertEqual(strip.locator(".oz-se-cap b").inner_text(), f"SE 0 · {strip_date(transit_series.get('date', ''))}")
        self.assertEqual(strip.locator(".oz-se-cap > span").inner_text(), "Scout")
        self.assertEqual(strip.locator(".oz-se-cap b").evaluate("el => getComputedStyle(el).textOverflow"), "clip")
        self.assertLessEqual(strip.locator(".oz-se-cap b").evaluate("el => el.scrollWidth"), strip.locator(".oz-se-cap b").evaluate("el => el.clientWidth"))

        mobile_context, mobile_page = self.open_page(f"#{study['id']}/{transit_index + 1}", width=375, transit_fixture=True)
        boxes = mobile_page.evaluate("""() => {
          const tl = document.querySelector('[data-ov=tl]').getBoundingClientRect();
          const tr = document.querySelector('[data-ov=tr]').getBoundingClientRect();
          return {left:tl.left, leftRight:tl.right, rightLeft:tr.left, right:tr.right, width:innerWidth};
        }""")
        self.assertLessEqual(boxes["leftRight"], boxes["rightLeft"], boxes)
        self.assertGreaterEqual(boxes["left"], 0)
        self.assertLessEqual(boxes["right"], boxes["width"])
        mobile_row = mobile_page.locator(f'.oz-row[href="#{study["id"]}"]')
        self.assertEqual(mobile_row.locator(".oz-card-tl").evaluate("el => getComputedStyle(el).display"), "none")
        self.assertEqual(mobile_row.locator(".oz-card-bl").evaluate("el => getComputedStyle(el).display"), "none")
        self.assertTrue(mobile_page.evaluate("""() => {
          const tr = document.querySelector('.oz-row .oz-card-tr').getBoundingClientRect();
          const br = document.querySelector('.oz-row .oz-card-br').getBoundingClientRect();
          return tr.bottom <= br.top || br.bottom <= tr.top || tr.right <= br.left || br.right <= tr.left;
        }"""))
        mobile_context.close()

        # Plain canonical routes, row clicks, and P/N browse to the first ordinary SE 1 image.
        page.evaluate(f"history.pushState(null, '', '#{study['id']}'); window.dispatchEvent(new PopStateEvent('popstate'))")
        self.assertTrue(self.current_source(page).startswith(study["images"][first_se1]["src"]))
        page.locator(f'[data-series] [data-se="{transit_series_index}"]').click()
        self.assertTrue(self.current_source(page).startswith(transit["src"]))
        page.keyboard.press("PageDown")
        page.wait_for_function("document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '1'")
        self.assertTrue(self.current_source(page).startswith(study["images"][first_se1]["src"]))
        page.evaluate("document.querySelector('[data-viewport]').dispatchEvent(new WheelEvent('wheel', {deltaY: -120, bubbles: true, cancelable: true}))")
        self.assertEqual(page.locator('[data-series] [aria-current="true"]').get_attribute("data-se"), "0")
        page.evaluate("document.querySelector('[data-viewport]').dispatchEvent(new WheelEvent('wheel', {deltaY: 120, bubbles: true, cancelable: true}))")
        self.assertEqual(page.locator('[data-series] [aria-current="true"]').get_attribute("data-se"), "1")
        page.keyboard.press("PageUp")
        page.wait_for_function("document.querySelector('[data-series] [aria-current=true]')?.dataset.se === '0'")
        self.assertEqual(self.current_source(page).startswith(transit["src"]), True)

        visible_ids = json.loads(page.locator("#oz-data").text_content() or "{}")["recentStudyIds"]
        self.assertIn(study["id"], visible_ids)
        page.locator(f'.oz-row[href="#{study["id"]}"]').click()
        self.assertTrue(self.current_source(page).startswith(study["images"][first_se1]["src"]))
        page.keyboard.press("N")
        next_study_id = visible_ids[(visible_ids.index(study["id"]) + 1) % len(visible_ids)]
        next_study = next(item for item in fixture_payload["studies"] if item["id"] == next_study_id)
        next_image = next(image for image in next_study["images"] if image.get("se") == 1)
        self.assertTrue(self.current_source(page).startswith(next_image["src"]))
        context.close()


if __name__ == "__main__":
    unittest.main()
