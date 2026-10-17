import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
const posts = await getCollection('blog');
posts.sort((a, b) => new Date(b.data.pubDate).valueOf() - new Date(a.data.pubDate).valueOf());

return rss({
title: 'News Internacional TEP | Dossier de Inteligencia',
description: 'Reportes monográficos, análisis geopolítico, mercados y prospectiva (Estándar MIT/Harvard).',
site: context.site || 'https://newsinternacionaltep.com',
items: posts.map((post) => ({
title: post.data.title,
description: post.data.description,
pubDate: post.data.pubDate,
link: '/blog/' + post.slug + '/',
})),
});
}