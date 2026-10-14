# 📋 Registro de Operaciones y Cambios TEP
*Documento de auditoría técnica y estética obligatoria.*

## [2026-10-14 02:23] - Restauración y Ajuste de Marquesinas
- **Archivos Modificados:** src/components/Header.astro
- **Objetivo:** Restaurar la estética original del logo y tipografías que fueron sobrescritas por error.
- **Cambios Aplicados:**
  1. Rollback (git checkout HEAD~1) para recuperar HTML y CSS intactos.
  2. Inyección de .tep-ticker-item con margen de 4.5rem para evitar que las letras se aplasten.
  3. Velocidad de animación ajustada a 150s para desplazamiento lento, legible y fluido.
  4. Protección lex-shrink: 0 en etiquetas rojas para evitar desbordamiento.
---
## 🛡️ DIRECTRIZ ESTRATÉGICA PERMANENTE (CÓDIGO DE CONDUCTA IA)
1. **ANÁLISIS PREVIO:** Antes de emitir cualquier bloque de código, la IA debe analizar la estructura existente.
2. **SINERGIA ESTRICTA:** Jamás borrar o sobrescribir archivos completos sin sentido. Toda modificación debe ser una inyección quirúrgica que respete la estética, tipografía y lógica ya lograda.
3. **CERO REGRESIONES:** El progreso solo avanza. Si un código nuevo rompe una funcionalidad previa, se hace rollback inmediato y se rediseña.
---

## [2026-10-14 03:15] - Habilitación Auto-Deploy y Motor SEO 3 Capas
- **Archivos Modificados:** .github/workflows/curate.yml, public/robots.txt (Nuevo), src/pages/rss.xml.js (Nuevo).
- **Objetivo:** Permitir que Cloudflare detecte los reportes del bot e indexe el sitio en Google/Bing.
- **Cambios Aplicados:**
  1. Eliminada la restricción [skip ci] en el flujo de GitHub Actions.
  2. Generado obots.txt permisivo apuntando al sitemap-index.xml de Astro.
  3. Construido endpoint dinámico ss.xml.js para sindicación automatizada.
## [2026-10-14 03:23] - HOTFIX: Falla de Compilación RSS en Cloudflare
- **Archivos Modificados:** src/pages/rss.xml.js
- **Objetivo:** Resolver el error de "Build failed" en Cloudflare causado por el generador RSS.
- **Cambios Aplicados:**
  1. Refactorización de ss.xml.js para añadir tolerancia a fallos. Si un artículo (ej. generado por el bot) tiene metadatos incompletos o fechas no parseables, el feed lo ignorará en lugar de abortar la compilación de Astro.
## [2026-10-14 03:33] - HOTFIX: Flujo de Git del Bot (Exit Code 128)
- **Archivos Modificados:** .github/workflows/curate.yml
- **Objetivo:** Resolver el error cannot pull with rebase: You have unstaged changes durante la publicación automatizada.
- **Cambios Aplicados:**
  1. Reordenado el flujo de comandos de Git. Ahora el bot hace git add . y git commit ANTES de ejecutar git pull --rebase.
  2. Esto asegura que los archivos generados por la IA estén empaquetados y Git pueda fusionar el historial limpiamente si hubo cambios manuales simultáneos.
## [2026-10-14 03:42] - FIX: Sintaxis de Concatenación en rss.xml.js
- **Archivos Modificados:** src/pages/rss.xml.js
- **Objetivo:** Resolver el error de Vite PARSE_ERROR: Unterminated regular expression.
- **Cambios Aplicados:**
  1. Reemplazo de plantillas literales con concatenación estándar en comillas simples: '/blog/' + post.slug + '/'.
  2. Uso de literales puros en PowerShell para evitar la supresión accidental de comillas por caracteres de escape.
## [2026-10-14 04:34] - REFACTOR: Filtro Semántico de Imágenes en curator_engine.py
- **Archivos Modificados:** curator_engine.py, TEP_CHANGELOG.md
- **Objetivo:** Prevenir discrepancias visuales (ej. evitar fotos de taxis urbanos en reportes de ciberinfraestructura).
- **Cambios Aplicados:**
  1. Integración de validación de palabras clave de ruido visual (	axi, car, street, driver, ehicle) en la selección de la foto de prensa original.
  2. Optimización del prompt de respaldo por IA para forzar la representación de centros de datos, servidores y redes de fibra óptica en lugar de transporte urbano.
## [2026-10-14 04:38] - HOTFIX Visual: Corrección de Portada en Artículo de Yandex
- **Archivos Modificados:** src/content/blog/2026-10-14-fragilidad-digital-de-asia-central-ante-ataques-a-yande.md
- **Objetivo:** Sustituir la fotografía de transporte urbano (taxi) por una representación gráfica de centros de datos y ciberinfraestructura.
## [2026-10-14 04:52] - REFACTOR AVANZADO: Sincronización con Directorio Global de 165 Medios
- **Archivos Modificados:** curator_engine.py, directorio_global_medios.txt, TEP_CHANGELOG.md
- **Objetivo:** Arbitraje visual y documental cruzado con 165 portales de referencia global (Geopolítica, Economía y Tecnología).
- **Cambios Aplicados:**
  1. Integración de la validación del Directorio Global TEP para la corroboración temática de los cables informativos.
  2. Blindaje absoluto contra discrepancias visuales (filtro estricto anti-ruido urbano para reportes de infraestructura).
## [2026-10-14 04:58] - HOTFIX Visual: Inserción de Imagen Oficial BBC en Artículo Yandex
- **Archivos Modificados:** src/content/blog/2026-10-14-fragilidad-digital-de-asia-central-ante-ataques-a-yande.md
- **Objetivo:** Sustituir la ilustración generada por la fotografía oficial de cobertura internacional de la BBC (ichef.bbci.co.uk).
## [2026-10-14 15:54] - UPGRADE: Motor Masivo (18 Papers), Cascada Multi-Modelo y Conector Local Gemma 4 E4B
- **Archivos Modificados:** curator_engine.py, TEP_CHANGELOG.md
- **Capacidades Nuevas:**
  1. Expansión a 18 publicaciones por ciclo distribuido entre Geopolítica, Economía y Tecnología.
  2. Cascada de modelos complejos (Gemini 2.5 Pro / 1.5 Pro / 3.8 Flash / 2.0 Flash) con reintentos para 503 y 429.
  3. Detección automática de LM Studio ([http://127.0.0.1:1234](http://127.0.0.1:1234)) para usar Gemma 4 E4B localmente sin límites.
  4. Persistencia atómica de history.json para evitar pérdidas ante interrupciones.