# REPORTE 05: SITEMAPS, INDEXACIÓN Y ALCANCE GLOBAL
**Arquitectura de Indexación Algorítmica Masiva e Ingesta para Motores Semánticos**

---

## 1. El Mapa del Sitio XML de Alta Capacidad (Sitemaps Estáticos)
Para garantizar que los motores de búsqueda tradicionales (Google, Bing, Yandex, Baidu) y los rastreadores web de Inteligencia Artificial (OpenAI GPTBot, Anthropic ClaudeBot, Google-Extended, PerplexityBot) indexen la totalidad del catálogo sin depender exclusivamente del crawling orgánico, se generó un archivo `sitemap.xml` estático en el directorio `public/` de cada dominio.

### Contenido de cada Sitemap XML:
- **Páginas Raíz e Institucionales**:
  - Portada Principal (`/`): `priority: 1.0`, `changefreq: daily`
  - Acerca de / Nosotros (`/about`): `priority: 0.8`, `changefreq: monthly`
  - Términos de Servicio (`/terminos`): `priority: 0.5`, `changefreq: monthly`
  - Política de Privacidad (`/privacidad`): `priority: 0.5`, `changefreq: monthly`
- **Páginas de Categoría**:
  - `/categoria/geopolitica`, `/categoria/economia`, `/categoria/tecnologia`, `/categoria/ciencia`, `/categoria/tendencias`: `priority: 0.9`, `changefreq: daily`
- **Hemeroteca Completa**:
  - 6,310 URLs canónicas de artículos con su fecha exacta de publicación `<lastmod>`, `changefreq: monthly` y `priority: 0.7`.

### Inventario de URLs por Dominio:
- **Edición Español**: `https://newsinternacionaltep.com/sitemap.xml` → **6,322 URLs** (1.35 MB)
- **Edición Inglés**: `https://international.newsinternacionaltep.com/sitemap.xml` → **6,322 URLs** (1.44 MB)
- **Edición Chino**: `https://china.newsinternacionaltep.com/sitemap.xml` → **6,322 URLs** (1.39 MB)
- **Gran Total Indexable**: **18,966 URLs Activas**

---

## 2. Protocolo IndexNow e Indexación Independiente por Lotes
Por instrucción prioritaria:
> *"Además cuanto termines de cambiar el idioma y crear el International (China) Indexa ambas de forma independiente para que no colapse y actualiza las de News Internacional TEP (original)... Estas se indexan Individuales para ampliar al máximo el alcance"*

### Especificación de la Notificación IndexNow:
1. **Clave Criptográfica**: `eaead898f86547568039b4c7c52111ee`
2. **Ubicación del Archivo Clave**: Servido directamente en la raíz de cada sitio (`/{KEY}.txt`).
3. **Endpoints de Notificación**:
   - `https://www.bing.com/indexnow`
   - `https://yandex.com/indexnow`
4. **Estrategia de Lotes Anticolapso (Safe-Batching)**:
   - En lugar de enviar un payload gigantesco que pudiera saturar los sockets de conexión o provocar códigos `429 Too Many Requests`, el motor dividió el catálogo de cada dominio en **64 lotes sucesivos de 100 URLs cada uno**.
   - Cada lote fue despachado de forma estrictamente independiente por dominio (`host` y `keyLocation` diferenciados), permitiendo que Bing, Yandex y sus redes de motores asociados procesen cada idioma en su índice geográfico nativo correspondiente.
