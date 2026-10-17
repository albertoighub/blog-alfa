import os
import shutil

dirs = [
    ("https://newsinternacionaltep.com", "C:/BIONIC_CORE/blog-alfa/public"),
    ("https://international.newsinternacionaltep.com", "C:/BIONIC_CORE/blog-international/public"),
    ("https://china.newsinternacionaltep.com", "C:/BIONIC_CORE/blog-china/public")
]

for base_url, pdir in dirs:
    sitemap_xml = os.path.join(pdir, "sitemap.xml")
    sitemap_0 = os.path.join(pdir, "sitemap-0.xml")
    sitemap_index = os.path.join(pdir, "sitemap-index.xml")
    
    # 1. sitemap-0.xml is a copy of the comprehensive sitemap.xml
    shutil.copyfile(sitemap_xml, sitemap_0)
    
    # 2. sitemap-index.xml pointing to sitemap-0.xml and sitemap.xml
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <sitemap>',
        f'    <loc>{base_url}/sitemap-0.xml</loc>',
        '    <lastmod>2026-10-17</lastmod>',
        '  </sitemap>',
        '  <sitemap>',
        f'    <loc>{base_url}/sitemap.xml</loc>',
        '    <lastmod>2026-10-17</lastmod>',
        '  </sitemap>',
        '</sitemapindex>'
    ]
    with open(sitemap_index, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    print(f"[✓] Generated sitemaps in {pdir}: sitemap.xml, sitemap-0.xml, sitemap-index.xml")
