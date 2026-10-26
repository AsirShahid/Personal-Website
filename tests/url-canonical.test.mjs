import assert from "node:assert/strict";
import test from "node:test";

import {
  needsSlashProbe,
  normalizeRequest,
  retiredPaths,
  slashedPath,
} from "../src/worker/canonical.mjs";

// `pageExists` mirrors the Worker's asset probe: true only when the slashed
// form of the requested path is a real page.
const target = (url, method = "GET", pageExists = true) =>
  normalizeRequest(new URL(url), method, pageExists);

test("canonical URLs are left alone", () => {
  assert.equal(target("https://asir.dev/"), null);
  assert.equal(target("https://asir.dev/outside/"), null);
  assert.equal(target("https://asir.dev/blog/"), null);
  assert.equal(target("https://asir.dev/rss.xml"), null);
  assert.equal(target("https://asir.dev/robots.txt"), null);
});

test("www and http both redirect to https://asir.dev", () => {
  assert.equal(target("https://www.asir.dev/"), "https://asir.dev/");
  assert.equal(target("https://www.asir.dev/outside/"), "https://asir.dev/outside/");
  assert.equal(target("http://asir.dev/outside/"), "https://asir.dev/outside/");
  assert.equal(target("http://www.asir.dev/blog/"), "https://asir.dev/blog/");
});

test("a missing trailing slash redirects in one hop for real pages", () => {
  assert.equal(target("https://asir.dev/outside", "GET", true), "https://asir.dev/outside/");
  assert.equal(target("https://asir.dev/blog", "GET", true), "https://asir.dev/blog/");
  assert.equal(target("https://asir.dev/blog/my-post", "GET", true), "https://asir.dev/blog/my-post/");
  assert.equal(target("https://www.asir.dev/outside", "GET", true), "https://asir.dev/outside/");
});

test("unknown paths are never redirected to a slashed twin", () => {
  assert.equal(target("https://asir.dev/this-does-not-exist", "GET", false), null);
});

test("file paths keep their shape", () => {
  assert.equal(target("https://asir.dev/rss.xml/"), "https://asir.dev/rss.xml");
  assert.equal(needsSlashProbe(new URL("https://asir.dev/rss.xml")), false);
});

test("the error page is never slash-suffixed", () => {
  assert.equal(target("https://asir.dev/404"), null);
  assert.equal(target("https://www.asir.dev/404"), "https://asir.dev/404");
  assert.equal(needsSlashProbe(new URL("https://asir.dev/404")), false);
});

test("stale sitemap path points at the current index", () => {
  assert.equal(target("https://asir.dev/sitemap.xml"), "https://asir.dev/sitemap-index.xml");
  assert.equal(target("https://www.asir.dev/sitemap.xml"), "https://asir.dev/sitemap-index.xml");
});

test("query strings survive normalization", () => {
  assert.equal(target("https://asir.dev/blog?page=2"), "https://asir.dev/blog/?page=2");
});

test("retired paths answer in one hop", () => {
  assert.equal(target("https://asir.dev/posts", "GET", true), null);
  assert.equal(target("https://asir.dev/blog/getting-started-with-astro", "GET", true), null);
  assert.equal(target("https://www.asir.dev/posts", "GET", false), "https://asir.dev/posts");
  assert.equal(needsSlashProbe(new URL("https://asir.dev/posts")), false);
});

test("preview hosts and unsafe methods are untouched", () => {
  assert.equal(target("https://asir.asirshahid.workers.dev/"), null);
  assert.equal(target("http://asir.dev/blog/", "POST"), null);
});

test("slashed form helper", () => {
  assert.equal(slashedPath("/outside"), "/outside/");
  assert.equal(slashedPath("/outside/"), "/outside/");
});

test("retired content answers 410", () => {
  for (const path of [
    "/posts",
    "/posts/",
    "/posts/introduction/",
    "/posts/category/sub-category/",
    "/notes",
    "/notes/go/basic/",
    "/search/",
    "/categories/",
    "/tags",
    "/blog/getting-started-with-astro",
    "/blog/getting-started-with-astro/",
    "/blog/web-performance-101/",
  ]) {
    assert.equal(retiredPaths(path), true, path);
  }
});

test("live content is not treated as retired", () => {
  for (const path of ["/", "/outside/", "/blog/", "/blog/some-real-post/", "/postscript", "/rss.xml"]) {
    assert.equal(retiredPaths(path), false, path);
  }
});
