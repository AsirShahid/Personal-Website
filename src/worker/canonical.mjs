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
// instead of retrying. Never add a page here that should exist: restore it.
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

/** asir.dev and www.asir.dev are ours; preview hosts are left alone. */
export function isOursHost(url) {
  const host = url.hostname.toLowerCase();
  return host === CANONICAL_HOST || host === `www.${CANONICAL_HOST}`;
}

/**
 * True when this request might need a trailing slash added. The Worker then
 * checks whether the slashed URL is a real page before redirecting, so an
 * unknown path answers 404 instead of bouncing through a 301.
 */
export function needsSlashProbe(url) {
  const pathname = url.pathname;

  if (pathname === "/" || pathname.endsWith("/")) return false;
  if (NO_TRAILING_SLASH.has(pathname)) return false;
  if (PATH_ALIASES[pathname]) return false;
  if (retiredPaths(pathname)) return false;

  return !pathname.slice(pathname.lastIndexOf("/") + 1).includes(".");
}

/** Slashed form of a path, used as the probe URL. */
export function slashedPath(pathname) {
  return pathname.endsWith("/") ? pathname : `${pathname}/`;
}

/**
 * Absolute URL to redirect to, or null when the request is already canonical.
 *
 * `pageExists` says whether the slashed form of an unslashed path is a real
 * page; the Worker resolves it from the assets binding first.
 */
export function normalizeRequest(url, method = "GET", pageExists = false) {
  if (!isOursHost(url)) return null;

  // A 301 on POST would turn it into a GET; let those through untouched.
  if (method !== "GET" && method !== "HEAD") return null;

  let pathname = PATH_ALIASES[url.pathname] ?? url.pathname;

  if (needsSlashProbe(url)) {
    // A retired path answers 410 directly, and an unknown path must not be
    // redirected to a slashed twin that 404s: only real pages get the slash.
    if (!pageExists) return null;
    pathname = slashedPath(pathname);
  }

  // A trailing slash on a file path is always wrong: /rss.xml/ -> /rss.xml.
  if (pathname !== "/" && pathname.endsWith("/")) {
    const trimmed = pathname.replace(/\/+$/, "");
    const lastSegment = trimmed.slice(trimmed.lastIndexOf("/") + 1);
    if (lastSegment.includes(".")) pathname = trimmed;
  }

  const isCanonical =
    url.protocol === "https:" && url.hostname === CANONICAL_HOST && pathname === url.pathname;

  if (isCanonical) return null;

  const target = new URL(url.toString());
  target.protocol = "https:";
  target.hostname = CANONICAL_HOST;
  target.port = "";
  target.pathname = pathname;
  return target.toString();
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
