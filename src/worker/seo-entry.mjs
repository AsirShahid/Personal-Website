// Cloudflare Worker entry wrapper for asir.dev.
//
// Cloudflare answers a matching static asset before the Worker, and the Astro
// adapter's handler serves prerendered pages straight from the assets binding,
// so `src/middleware.ts` never sees them. Host, trailing-slash and retired-URL
// rules therefore have to run here, in front of the Astro handler.
//
// scripts/wrap-worker-entry.mjs installs this file as dist/server/entry.mjs
// after every build: the adapter's own entry is kept as ./entry.astro.mjs and
// re-exported through this wrapper. `assets.run_worker_first` in
// wrangler.jsonc sends page paths here while leaving /_astro/* build output
// and the Outside photo derivatives on the pure asset path.

import astro from "./entry.astro.mjs";
import {
  needsSlashProbe,
  normalizeRequest,
  retiredPaths,
  RETIRED_HTML,
  slashedPath,
} from "./canonical.mjs";

async function assetExists(env, url, pathname) {
  const probe = new URL(url.toString());
  probe.pathname = pathname;

  try {
    const response = await env.ASSETS.fetch(new Request(probe, { method: "HEAD" }));
    await response.body?.cancel();
    return response.status < 400;
  } catch {
    return false;
  }
}

async function gone(env, url) {
  // Reuse the prerendered 404 page so a retired URL still looks like the site.
  let body = RETIRED_HTML;
  let contentType = "text/html; charset=utf-8";

  try {
    const page = await env.ASSETS.fetch(new URL("/404.html", url));
    if (page.ok) {
      body = page.body ?? RETIRED_HTML;
      contentType = page.headers.get("Content-Type") ?? contentType;
    } else {
      await page.body?.cancel();
    }
  } catch {
    // Fall through to the plain fallback body.
  }

  return new Response(body, {
    status: 410,
    headers: {
      "Content-Type": contentType,
      "X-Robots-Tag": "noindex",
      "Cache-Control": "public, max-age=3600",
    },
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (retiredPaths(url.pathname)) {
      return gone(env, url);
    }

    // Only redirect a missing trailing slash when the slashed URL is a real
    // page; an unknown path must answer 404, not 301.
    const pageExists =
      needsSlashProbe(url) && (await assetExists(env, url, slashedPath(url.pathname)));

    const redirectTo = normalizeRequest(url, request.method, pageExists);
    if (redirectTo) {
      return new Response(null, { status: 301, headers: { Location: redirectTo } });
    }

    const response = await astro.fetch(request, env, ctx);

    // /404 is a real file; it must never answer 200 and get indexed.
    if (response.status === 200 && /^\/404\/?$/.test(url.pathname)) {
      const headers = new Headers(response.headers);
      headers.set("X-Robots-Tag", "noindex");
      return new Response(response.body, { status: 404, headers });
    }

    return response;
  },
};
