// URL rules for asir.dev, shared by the Worker entry and its tests.
//
// Plain ESM on purpose: this module is copied verbatim into dist/server at
// build time (see scripts/wrap-worker-entry.mjs) where Wrangler uploads it
// unbundled, and node:test imports it directly.

export const CANONICAL_HOST = "asir.dev";

// Paths whose canonical form is a different URL.
export const PATH_ALIASES = {
  // Google was handed /sitemap.xml by the pre-2026 Hugo site. The current
  // sitemap is the @astrojs/sitemap index that robots.txt points at.
  "/sitemap.xml": "/sitemap-index.xml",
};

// Astro's error page is built as 404.html, which is served at /404.
const NO_TRAILING_SLASH = new Set(["/404"]);

// URLs that used to exist and were deliberately retired: template articles
// from the Astro starter (removed in 735f23e, "remove template leftovers") and
// the demo /posts and /notes content of the Hugo site the Astro rewrite
// replaced (a0819b5). They answer 410 Gone, not 404, so Google drops them
// instead of retrying. Do not add a page here that should exist: restore it.
export const RETIRED_PREFIXES = ["/posts", "/notes", "/search", "/categories", "/tags", "/series"];

export const RETIRED_BLOG_SLUGS = [
  "building-restful-apis",
  "css-grid-complete-guide",
  "getting-started-with-astro",
  "intro-to-web-accessibility",
  "javascript-async-await",
  "state-management-patterns",
  "web-performance-101",
];

function trimTrailingSlash(path) {
  return path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path;
}

function lastSegment(pathname) {
  return pathname.slice(pathname.lastIndexOf("/") + 1);
}

/** Canonical form of a path is always slashed, except files and /404. */
export function normalizeTrailingSlash(pathname) {
  if (pathname === "/") return pathname;

  const segment = lastSegment(pathname);

  if (pathname.endsWith("/")) {
    // /rss.xml/ -> /rss.xml, but leave directory paths alone.
    const beforeSlash = pathname.replace(/\/+$/, "");
    return beforeSlash.includes(".") ? beforeSlash : pathname;
  }

  if (NO_TRAILING_SLASH.has(pathname)) return pathname;
  if (segment.includes(".")) return pathname;

  return `${pathname}/`;
}

/**
 * Absolute URL to redirect to, or null when the request is already canonical.
 * Only asir.dev and www.asir.dev are touched so preview hosts keep working.
 */
export function normalizeRequest(url, method = "GET") {
  const host = url.hostname.toLowerCase();
  const isApex = host === CANONICAL_HOST;
  const isWww = host === `www.${CANONICAL_HOST}`;

  if (!isApex && !isWww) return null;

  // A 301 on POST would turn it into a GET; let those through untouched.
  if (method !== "GET" && method !== "HEAD") return null;

  let pathname = PATH_ALIASES[url.pathname] ?? url.pathname;
  pathname = normalizeTrailingSlash(pathname);

  if (url.protocol === "https:" && isApex && pathname === url.pathname) return null;

  const target = new URL(url.toString());
  target.protocol = "https:";
  target.hostname = CANONICAL_HOST;
  target.port = "";
  target.pathname = pathname;
  return target.toString();
}

/** True when the path belongs to permanently removed content. */
export function retiredPaths(pathname) {
  const path = trimTrailingSlash(pathname);

  for (const prefix of RETIRED_PREFIXES) {
    if (path === prefix || path.startsWith(`${prefix}/`)) return true;
  }

  if (path.startsWith("/blog/")) {
    return RETIRED_BLOG_SLUGS.includes(path.slice("/blog/".length));
  }

  return false;
}

// Fallback body when the prerendered 404 page cannot be read from the assets
// binding.
export const RETIRED_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>410 - Gone | Asir Shahid</title></head>
<body style="font-family:system-ui,sans-serif;max-width:36rem;margin:15vh auto;padding:0 1.5rem">
<h1>410 - Gone</h1>
<p>This page was permanently removed and will not be coming back.</p>
<p><a href="/">Go to the homepage</a></p>
</body></html>`;
