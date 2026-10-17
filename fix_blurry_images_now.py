import glob
import os
import re

# Curated, crystal-clear 1200px Unsplash editorial images for economics, markets, tech, and defense
high_res_pool = {
    "econ": [
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&h=630&q=85"
    ],
    "geo": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&h=630&q=85"
    ],
    "tech": [
        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&h=630&q=85",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&h=630&q=85"
    ]
}

files = glob.glob("src/content/blog/*.md")
fixed = 0

for f in files:
    content = open(f, encoding="utf-8").read()
    for line in content.splitlines()[:15]:
        if line.startswith("heroImage:"):
            u = line.split("heroImage:")[1].strip(" \"'")
            needs_fix = False
            pool_key = "econ"
            if "jornaldenegocios.pt" in u or "100x100" in u or "150x" in u or "200x" in u:
                needs_fix = True
                pool_key = "econ"
            elif "kyivindependent" in u:
                needs_fix = True
                pool_key = "geo"
            elif "bonniernews" in u:
                needs_fix = True
                pool_key = "econ"
                
            if needs_fix:
                replacement = high_res_pool[pool_key][fixed % len(high_res_pool[pool_key])]
                content = content.replace(u, replacement)
                with open(f, "w", encoding="utf-8") as out:
                    out.write(content)
                fixed += 1
                print(f"[✓] Fixed blurry image in {os.path.basename(f)} -> {replacement[:55]}...")
                break

print(f"Total blurry images replaced with razor-sharp 1200px HD photos: {fixed}")
