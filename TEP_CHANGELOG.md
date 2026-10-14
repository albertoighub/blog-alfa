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