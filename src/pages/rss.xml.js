import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
    try {
        const posts = await getCollection('blog');
        
        const validPosts = posts
            .filter(post => post && post.data && post.data.title && post.data.pubDate)
            .sort((a, b) => {
                const dateA = new Date(a.data.pubDate).valueOf();
                const dateB = new Date(b.data.pubDate).valueOf();
                return dateB - dateA;
            });
        
        return rss({
            title: 'News Internacional TEP | Dossier de Inteligencia',
            description: 'Reportes monográficos, análisis geopolítico, mercados y prospectiva (Estándar MIT/Harvard).',
            site: context.site || 'https://newsinternacionaltep.com',
            items: validPosts.map((post) => ({
                title: post.data.title,
                description: post.data.description || '',
                pubDate: post.data.pubDate,
                // FIX: Uso correcto de backticks para la interpolación de cadenas
                link: /blog/ + post.slug + /,
            })),
        });
    } catch (error) {
        console.error("Error crítico generando el feed RSS:", error);
        return rss({
            title: 'News Internacional TEP (Fallback)',
            description: 'Feed temporalmente en mantenimiento.',
            site: context.site || 'https://newsinternacionaltep.com',
            items: [],
        });
    }
}