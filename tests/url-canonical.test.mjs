import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizeRequest,
  normalizeTrailingSlash,
  retiredPaths,
} from "../src/worker/canonical.mjs";

const target = (url, method = "GET") => normalizeRequest(new URL(url), method);

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

test("missing trailing slash redirects in one hop", () => {
  assert.equal(target("https://asir.dev/outside"), "https://asir.dev/outside/");
  assert.equal(target("https://asir.dev/blog"), "https://asir.dev/blog/");
  assert.equal(target("https://asir.dev/blog/my-post"), "https://asir.dev/blog/my-post/");
  // www plus a missing slash still lands in one redirect
  assert.equal(target("https://www.asir.dev/outside"), "https://asir.dev/outside/");
  // file paths keep their shape
  assert.equal(target("https://asir.dev/rss.xml"), null);
  assert.equal(target("https://asir.dev/rss.xml/"), "https://asir.dev/rss.xml");
});

test("the error page stays at /404 and is never slash-suffixed", () => {
  assert.equal(target("https://asir.dev/404"), null);
  assert.equal(target("https://www.asir.dev/404"), "https://asir.dev/404");
});

test("stale sitemap path points at the current index", () => {
  assert.equal(target("https://asir.dev/sitemap.xml"), "https://asir.dev/sitemap-index.xml");
  assert.equal(target("https://www.asir.dev/sitemap.xml"), "https://asir.dev/sitemap-index.xml");
});

test("query strings survive normalization", () => {
  assert.equal(target("https://asir.dev/blog?page=2"), "https://asir.dev/blog/?page=2");
});

test("retired paths answer in one hop", () => {
  assert.equal(target("https://asir.dev/posts"), null);
  assert.equal(target("https://asir.dev/blog/getting-started-with-astro"), null);
  assert.equal(target("https://www.asir.dev/posts"), "https://asir.dev/posts");
});

test("preview hosts and unsafe methods are untouched", () => {
  assert.equal(target("https://asir.asirshahid.workers.dev/"), null);
  assert.equal(target("http://asir.dev/blog/", "POST"), null);
});

test("trailing-slash shaping", () => {
  assert.equal(normalizeTrailingSlash("/"), "/");
  assert.equal(normalizeTrailingSlash("/outside"), "/outside/");
  assert.equal(normalizeTrailingSlash("/outside/"), "/outside/");
  assert.equal(normalizeTrailingSlash("/sitemap-0.xml"), "/sitemap-0.xml");
  assert.equal(normalizeTrailingSlash("/rss.xml/"), "/rss.xml");
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
