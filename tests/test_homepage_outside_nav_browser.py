import os
import unittest
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("OUTSIDE_CANDIDATE_URL", "http://127.0.0.1:4321/")
EVIDENCE_DIR = Path(os.environ.get("OUTSIDE_EVIDENCE_DIR", "/tmp/outside-nav-browser"))
EXPECTED_PATHS = ["/", "/blog", "/outside"]


class HomepageOutsideNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.webkit.launch(headless=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_outside_link_follows_blog_and_opens_viewer(self):
        errors = []
        context = self.browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(BASE_URL, wait_until="domcontentloaded")
        self.assertEqual(getattr(response, "status", None), 200)
        page.wait_for_function(
            "() => { const island = document.querySelector('astro-island[component-url*=\"NavbarIsland\"]'); return island && !island.hasAttribute('ssr'); }",
            timeout=10000,
        )

        links = page.locator('[class~="fixed"][class~="bottom-4"] a[href]').evaluate_all(
            "nodes => nodes.filter(node => ['/', '/blog', '/outside'].includes(node.getAttribute('href'))).map(node => ({href: node.getAttribute('href'), label: node.getAttribute('aria-label'), iconHidden: node.querySelector('svg')?.getAttribute('aria-hidden')}))"
        )
        self.assertEqual([item["href"] for item in links], EXPECTED_PATHS, links)
        self.assertEqual([item["label"] for item in links], EXPECTED_PATHS, links)
        self.assertTrue(all(item["iconHidden"] == "true" for item in links), links)

        home_link = page.get_by_role("link", name="/", exact=True)
        blog_link = page.get_by_role("link", name="/blog", exact=True)
        outside_link = page.get_by_role("link", name="/outside", exact=True)
        blog_link.hover()
        page.get_by_role("tooltip").get_by_text("Blog", exact=True).wait_for(state="visible", timeout=3000)
        for link in (home_link, blog_link, outside_link):
            link.focus()
            self.assertTrue(link.evaluate("element => element === document.activeElement"))

        outside_hover_page = context.new_page()
        outside_hover_page.on("pageerror", lambda error: errors.append(str(error)))
        outside_hover_response = outside_hover_page.goto(BASE_URL, wait_until="domcontentloaded")
        self.assertEqual(getattr(outside_hover_response, "status", None), 200)
        outside_hover_page.wait_for_function(
            "() => { const island = document.querySelector('astro-island[component-url*=\"NavbarIsland\"]'); return island && !island.hasAttribute('ssr'); }",
            timeout=10000,
        )
        outside_hover_page.get_by_role("link", name="/outside", exact=True).hover()
        outside_hover_page.get_by_role("tooltip").get_by_text("/outside", exact=True).wait_for(state="visible", timeout=3000)

        desktop_scroll_width = outside_hover_page.evaluate("document.documentElement.scrollWidth")
        self.assertLessEqual(desktop_scroll_width, 1280)
        outside_hover_page.screenshot(path=str(EVIDENCE_DIR / "homepage-desktop-1280x900.png"))

        mobile = context.new_page()
        mobile.set_viewport_size({"width": 390, "height": 844})
        mobile.on("pageerror", lambda error: errors.append(str(error)))
        mobile_response = mobile.goto(BASE_URL, wait_until="domcontentloaded")
        self.assertEqual(getattr(mobile_response, "status", None), 200)
        mobile.wait_for_function(
            "() => { const island = document.querySelector('astro-island[component-url*=\"NavbarIsland\"]'); return island && !island.hasAttribute('ssr'); }",
            timeout=10000,
        )
        self.assertLessEqual(mobile.evaluate("document.documentElement.scrollWidth"), 390)
        mobile.screenshot(path=str(EVIDENCE_DIR / "homepage-mobile-390x844.png"))

        outside_responses = []
        mobile.on(
            "response",
            lambda response: outside_responses.append(response.status)
            if response.request.is_navigation_request() and urlparse(response.url).path.rstrip("/") == "/outside"
            else None,
        )
        mobile.get_by_role("link", name="/outside", exact=True).click()
        mobile.wait_for_url("**/outside/**", timeout=10000)
        self.assertEqual(urlparse(mobile.url).path.rstrip("/"), "/outside")
        self.assertEqual(mobile.title(), "Outside Studies | Asir Shahid")
        self.assertTrue(mobile.get_by_role("heading", name="Outside Studies", exact=True).is_visible())
        self.assertIn(200, outside_responses, outside_responses)
        first_study = mobile.locator("[data-study]").first
        self.assertTrue(first_study.is_visible())
        first_study.click()
        mobile.wait_for_function("document.body.classList.contains('is-reading')", timeout=10000)
        self.assertTrue(mobile.locator("[data-viewport][aria-roledescription='image stack viewer']").is_visible())
        mobile.wait_for_function("document.querySelector('[data-cells] img')?.naturalWidth > 0", timeout=10000)
        self.assertEqual(errors, [], errors)
        context.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
