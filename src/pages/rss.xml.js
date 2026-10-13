import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
const posts = await getCollection('blog');
const sortedPosts = posts.sort(
(a, b) => new Date(b.data.pubDate).valueOf() - new Date(a.data.pubDate).valueOf()
);

return rss({
title: 'News Internacional TEP',
description: 'Análisis independiente en Tecnología, Economía y Política Global.',
site: 'https://newsinternacionaltep.com',
items: sortedPosts.map((post) => ({
title: post.data.title,
pubDate: post.data.pubDate,
description: post.data.description,
link: `/blog/${post.slug ?? post.id}/`,
})),
customData: `<language>es-mx</language>`,
});
}
