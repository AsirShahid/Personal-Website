# asir.dev

Personal website for Asir Shahid: medical student in the Three-Year MD Program at Stony Brook's Renaissance School of Medicine, Class of 2029. Formerly a Data Scientist at Goldman Sachs and an Automation Engineer at Zebra Technologies.

Live at [asir.dev](https://asir.dev).

## Stack

- [Astro v6](https://astro.build) — static site framework
- [React](https://react.dev) — interactive components
- [Tailwind CSS v4](https://tailwindcss.com)
- [TypeScript](https://www.typescriptlang.org)
- Deployed on [Cloudflare Workers](https://workers.cloudflare.com)

## Development

```bash
pnpm install
pnpm dev
```

## Build

```bash
pnpm build
```

All site content lives in `src/data/resume.tsx`.

## Deploy

```bash
pnpm run deploy
```

Deploys to Cloudflare Workers via Wrangler (requires `wrangler login` or a `CLOUDFLARE_API_TOKEN`).

### Domains

`asir.dev` and `www.asir.dev` are attached to the Worker as custom domains
(`wrangler.jsonc`). The `www → asir.dev` redirect for prerendered pages must
be a zone-level **Redirect Rule** in the Cloudflare dashboard (Rules →
Redirect Rules), because static assets are served before any Worker or
middleware code runs. The middleware in `src/middleware.ts` only covers
server-rendered routes.

## Credits

Based on the Starfolio Astro template by websiterating.
