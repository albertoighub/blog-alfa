with open("src/pages/index.astro", "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    ('<html lang="es">', '<html lang="en">'),
    ('Publicaciones en Rotación Continua', 'Continuous Rotation Editorial Stream'),
    ('FLUJO EN VIVO', 'LIVE INTEL STREAM'),
    ('aria-label="Pausar o Reanudar rotación">⏸ Pausar</button>', 'aria-label="Pause or Resume Stream">⏸ Pause</button>'),
    ('toggleBtn.textContent = "▶ Reanudar";', 'toggleBtn.textContent = "▶ Resume";'),
    ('toggleBtn.textContent = "⏸ Pausar";', 'toggleBtn.textContent = "⏸ Pause";'),
    ('<span>RADAR DE COBERTURA</span>', '<span>INTELLIGENCE RADAR</span>'),
    ('<span style="font-size: 0.65rem; color: #dc2626;">MONITOREO EN VIVO</span>', '<span style="font-size: 0.65rem; color: #dc2626;">LIVE DISPATCH</span>'),
    ('<span>Acceder al Dossier Completo</span>', '<span>Access Full Dossier</span>'),
    ('Investigación crítica sobre perfilamiento algorítmico no consentido, filtros de sesgo automatizados y la vulnerabilidad sociológica de los postulantes en la era digital.', 'Critical investigation on non-consensual algorithmic profiling, automated bias filters, and the sociological vulnerability of applicants in the digital age.'),
    ('ESPACIO PUBLICITARIO INSTITUCIONAL • GOOGLE ADSENSE (ca-pub-3739732712037306)', 'INSTITUTIONAL SPONSORED PLACEMENT • GOOGLE ADSENSE (ca-pub-3739732712037306)'),
    ('Política & Orden Global', 'Politics & Global Strategy'),
    ('Economía & Mercados Financieros', 'Economy & Global Financial Markets'),
    ('Tecnología & Inteligencia Artificial', 'Technology & Frontier AI'),
    ('Ciencia & Medicina de Frontera', 'Frontier Science & Biomedicine'),
    ('Redes Sociales & Noticias de Alto Revuelo', 'Social Dynamics & Cultural Trends'),
    ('Ver sección completa →', 'Explore Full Section →'),
    ('• TEP Política', '• TEP Politics'),
    ('• TEP Mercados', '• TEP Markets'),
    ('• TEP Tecnología', '• TEP Technology'),
    ('• TEP Ciencia', '• TEP Science'),
    ('• TEP Dinámica Digital', '• TEP Digital Dynamics'),
    ('INDEPENDENCIA ANALÍTICA & RIGOR EDITORIAL', 'ANALYTICAL INDEPENDENCE & RIGOROUS INVESTIGATION'),
    ('Impulsa el Archivo Libre de News Internacional TEP', 'Empower the Open Archive of News International TEP'),
    ('Nuestra redacción e infraestructura técnica operan sin subsidios corporativos ni censura partidista. Tu contribución directa a través de PayPal fortalece nuestros servidores de análisis, la ingesta continua de cables de datos y el acceso abierto a la inteligencia global.', 'Our analytical editorial team and technical infrastructure operate without corporate subsidies or partisan bias. Your direct PayPal contribution sustains our high-performance servers, continuous data ingestion, and unrestricted open access to global intelligence.'),
    ('<span>Donar con PayPal Oficial</span>', '<span>Support with Official PayPal</span>'),
    ('Titular: andredateig@gmail.com', 'Beneficiary: andredateig@gmail.com'),
    ('/categoria/geopolitica', '/category/geopolitics'),
    ('/categoria/economia', '/category/economy'),
    ('/categoria/tecnologia', '/category/technology'),
    ('/categoria/ciencia', '/category/science'),
    ('/categoria/tendencias', '/category/trends'),
    ("'es-MX'", "'en-US'")
]

for old, new in replacements:
    content = content.replace(old, new)

with open("src/pages/index.astro", "w", encoding="utf-8") as f:
    f.write(content)

print("index.astro in blog-international successfully localized to English.")
