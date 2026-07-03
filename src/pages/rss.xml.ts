import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { DATA } from "@/data/resume";
import { CONFIG } from "@/data/config";
import type { APIRoute } from "astro";

export const prerender = true;

export const GET: APIRoute = async (context) => {
  const posts = await getCollection("blog");
  const sortedPosts = [...posts].sort(
    (a, b) =>
      new Date(b.data.publishedAt).getTime() -
      new Date(a.data.publishedAt).getTime()
  );

  return rss({
    title: `${DATA.name} — Blog`,
    description: DATA.description,
    site: context.site ?? CONFIG.site.url,
    items: sortedPosts.map((post) => ({
      title: post.data.title,
      description: post.data.summary,
      pubDate: new Date(post.data.publishedAt),
      link: `/blog/${post.id}`,
    })),
  });
};
