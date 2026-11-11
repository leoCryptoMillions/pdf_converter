# Calidad del MVP y cierre reproducible

Actualizado: 2026-11-10 · 0.7.0. El piloto de cinco documentos de 0.6.4 fue
aceptado por el usuario el 2026-10-28. Las pruebas técnicas posteriores protegen
su recorrido; no sustituyen la adjudicación representativa pendiente del Gate F0.

Durante desarrollo se usa `python -m pytest -q`, selección `mvp` por riesgo.
Se conserva la suite completa con `-m "mvp or not mvp"`; el número de casos se
consulta con `--collect-only`, sin fijar una proporción exacta histórica.
Toda modificación ejecuta además los casos completos del módulo afectado.

## Cierre de entrega

Instalar `requirements-mvp-dev.lock` con `--require-hashes`, ejecutar `npm ci`
y `npx playwright install chromium`, después:

```powershell
python -m scripts.check_release --audit
```

El comando exige éxito en consistencia de dependencias, regresión completa,
cobertura de ramas de `apps`/`packages` (70% mínimo), inventario técnico, build
del wheel, instalación en un entorno vacío fuera del árbol fuente, conversión
CLI/HTTP, descargas, edición/guardado/reapertura de DOCX/XLSX con sus bibliotecas,
flujo Chromium y guardar/cancelar/exportar del dashboard. La auditoría consulta
vulnerabilidades y escribe un SBOM CycloneDX. Los pasos/códigos de salida quedan
en `.generated/release-check/report.json`, con cobertura en `coverage.json`.
La opción `--skip-browser` identifica una comprobación parcial; sin `--audit`
se registra que no se consultó vulnerabilidades en esa ejecución.

La cobertura incluye los esqueletos de plataforma futura, sin excluirlos para
mejorar el porcentaje. No demuestra la calidad visual de todos los documentos.
Los casos de HTTP/instalación generan PDFs ficticios y no necesitan el corpus
privado. La prueba de OCR real se omite si faltan sus dependencias opcionales;
el límite Windows se prueba con una asignación que excede un Job Object real.

La matriz manual Windows/Linux está declarada en el workflow, sin ejecutar
Actions automáticamente. El informe de esta entrega distingue la ejecución
local Windows de cualquier validación Linux pendiente.

## Regresiones protegidas

- Configuración parcial de acceso, Unicode, Host/cliente/origen y caché.
- Límite de carga antes del spool, multipart extra, bytes reales y admisión.
- IPC grande, timeout, caída del hijo, memoria y permiso durante cancelación.
- Publicación completa, limpieza inicial, trabajo activo y descarga vencida.
- Advertencias de documento, página, bloque, tabla, celda y exportación.
- Integridad de texto, procedencia, fórmulas XLSX, documentos editables y recursos.
- Temas, teclado/foco, tamaños móviles, ayuda y recorrido sin JavaScript.

La revisión humana del piloto y las mediciones históricas de CER/F1 conservan
sus límites y referencias en AVANCE.md. Corpus, adjudicación amplia, licencias
de distribución y costos requieren decisiones adicionales para cerrar Gate F0.
