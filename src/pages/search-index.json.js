import { getCollection } from 'astro:content';

export async function GET() {
const posts = await getCollection('blog');
const searchData = posts.map((post) => ({
id: post.slug ?? post.id,
title: post.data.title,
description: post.data.description,
pubDate: post.data.pubDate.toISOString().split('T')[0],
category: post.data.category || 'General',
tags: post.data.tags || [],
author: post.data.author || 'Comité Analítico TEP',
url: `/blog/${post.slug ?? post.id}/`,
heroImage: post.data.heroImage || ''
}));

return new Response(JSON.stringify(searchData), {
headers: {
'Content-Type': 'application/json'
}
});
}