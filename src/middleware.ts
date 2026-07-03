import { defineMiddleware } from "astro:middleware";

const CANONICAL_HOST = "asir.dev";

// Astro middleware only runs for server-rendered routes — the Cloudflare
// adapter serves prerendered pages straight from static assets, where
// public/_headers supplies these same headers and a zone-level Redirect Rule
// (Cloudflare dashboard) must handle the www -> apex redirect. This
// middleware covers the SSR routes, which _headers and _redirects never see.
const SECURITY_HEADERS: Record<string, string> = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

export const onRequest = defineMiddleware(async (context, next) => {
  const url = new URL(context.request.url);
  const headerHost = context.request.headers.get("host") ?? "";

  if (
    url.hostname === `www.${CANONICAL_HOST}` ||
    headerHost === `www.${CANONICAL_HOST}`
  ) {
    url.hostname = CANONICAL_HOST;
    url.protocol = "https:";
    url.port = "";
    return new Response(null, {
      status: 301,
      headers: { Location: url.toString(), ...SECURITY_HEADERS },
    });
  }

  const response = await next();
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    if (!response.headers.has(key)) {
      response.headers.set(key, value);
    }
  }
  return response;
});
