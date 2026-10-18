// @ts-check
import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';
import tailwindcss from '@tailwindcss/vite';
import react from '@astrojs/react';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import remarkGfm from 'remark-gfm';
import rehypePrettyCode from 'rehype-pretty-code';
import { remarkCodeMeta } from './src/lib/remark-code-meta.ts';
import { CONFIG } from './src/data/config.ts';

/** @type {import('rehype-pretty-code').Options} */
const prettyCodeOptions = {
  theme: {
    light: 'github-light',
    dark: 'github-dark',
  },
  keepBackground: false,
};

// Astro names a page's CSS after its module, e.g. "outside@_@astro.<hash>.css". Cloudflare answers any "@" in a
// path with a 307 to "%40", so every visit paid an extra round trip before its render-blocking stylesheet. Same
// names and hashes as the default "_astro/[name].[hash][extname]", with "@" written as "_".
/** @param {{ names?: string[], name?: string }} asset */
const assetFileNames = (asset) => {
  const name = (asset.names?.[0] ?? asset.name ?? 'asset').replace(/\.[^./]*$/, '');
  return `_astro/${name.replaceAll('@', '_')}.[hash][extname]`;
};

// https://astro.build/config
export default defineConfig({
  site: CONFIG.site.url,
  output: 'server',
  adapter: cloudflare(),

  vite: {
    plugins: [tailwindcss()],
    build: { rollupOptions: { output: { assetFileNames } } },
    environments: { client: { build: { rollupOptions: { output: { assetFileNames } } } } },
  },

  integrations: [
    react(),
    mdx({
      remarkPlugins: [remarkGfm, remarkCodeMeta],
      rehypePlugins: [[rehypePrettyCode, prettyCodeOptions]],
      syntaxHighlight: false,
    }),
    sitemap(),
  ],

  markdown: {
    syntaxHighlight: false,
    remarkPlugins: [remarkGfm, remarkCodeMeta],
    rehypePlugins: [[rehypePrettyCode, prettyCodeOptions]],
  },
});
