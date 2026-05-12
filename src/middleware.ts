import { defineMiddleware } from "astro:middleware";

export const onRequest = defineMiddleware((context, next) => {
  const host = context.request.headers.get("host") ?? "";
  const canonical = "asir.dev";

  if (host === "asirshahid.com" || host === "www.asirshahid.com") {
    const url = new URL(context.request.url);
    url.hostname = canonical;
    return Response.redirect(url.toString(), 301);
  }

  return next();
});
