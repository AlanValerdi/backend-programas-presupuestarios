# Formato de Evidencia — Variables de plantilla

Plantilla: `app/Formato de Evidencia - Cumplimiento de Metas - Copy.docx`

Este documento describe las variables `docxtpl` usadas en la plantilla, su origen de datos y los campos pendientes por modelar en la base de datos.

## Sección 1 — Datos de identificación del programa

| Variable | Descripción | Fuente actual | Estado |
|----------|-------------|---------------|--------|
| `{{ dependencia_responsable }}` | Dependencia o entidad responsable | `programa.unidad_administrativa.nombre` (unidad del usuario capturista / programa) | Disponible |
| `{{ programa_presupuestario }}` | Clave y nombre del programa presupuestario | `programa.clave` + `programa.programa` | Disponible |
| `{{ eje_pmd }}` | Eje del Plan Municipal de Desarrollo | — | **Pendiente** — no existe campo de eje estratégico en BD |
| `{{ trimestre_reporte }}` | Trimestre y ejercicio fiscal | Derivado de `mes` → `((mes-1)//3)+1` + `programa.ejercicio.anio` | Disponible |

## Sección 2 — Datos del indicador y meta

| Variable | Descripción | Fuente actual | Estado |
|----------|-------------|---------------|--------|
| `{{ nivel_mir }}` | Nivel en la MIR | Valor fijo `"Actividad"` | Parcial — no hay campo explícito en BD |
| `{{ nombre_indicador }}` | Nombre del indicador | `actividad.descripcion` | Disponible |
| `{{ unidad_medida }}` | Unidad de medida | — | **Pendiente** — no existe en BD |
| `{{ meta_programada_periodo }}` | Meta programada del periodo | `ProgramacionMeta.cantidad_programada` (mes seleccionado) | Disponible |
| `{{ meta_alcanzada }}` | Meta alcanzada (realizada) | `ProgramacionAvance.avance_meta` (mes seleccionado) | Disponible |
| `{{ porcentaje_cumplimiento }}` | Porcentaje de cumplimiento con fórmula | `(alcanzada / programada) * 100` calculado en servicio | Disponible |

Formato de `porcentaje_cumplimiento`: `(alcanzada / programada) * 100 = XX.XX%`. Si `programada == 0`, se muestra `N/A`.

## Sección 3 — Descripción de la evidencia documental

| Variable | Descripción | Fuente actual | Estado |
|----------|-------------|---------------|--------|
| `{% for ev in evidencias_documentales %}` | Lista de evidencias del mes | `ProgramacionAvance.evidencias` activas del mes seleccionado | Disponible |
| `{{ ev.tipo_documento }}` | Tipo de documento adjunto | Capturado por archivo en frontend | Disponible |
| `{{ ev.folios_referencias }}` | Folios o referencias | Capturado por archivo en frontend | Disponible |
| `{{ ev.ubicacion_archivo }}` | Ubicación del archivo | URL de descarga `{base_url}/api/programas/evidencia/download/{evidencia_id}` | Disponible |
| `{{ ev.nombre_archivo }}` | Nombre original del archivo | `ProgramacionEvidencia.nombre_original` | Disponible |

## Sección 4 — Análisis y justificación

| Variable | Descripción | Fuente actual | Estado |
|----------|-------------|---------------|--------|
| `{{ justificacion_tecnica }}` | Justificación técnica/administrativa | Capturada en frontend (`/capturista-pp/reportedoc/[id]?mes=`) y enviada en el POST al backend | Disponible |

## Sección 5 — Firmas de validación

| Variable | Descripción | Fuente actual | Estado |
|----------|-------------|---------------|--------|
| `{{ elaboro_nombre_cargo }}` | Nombre y cargo de quien elaboró | — | **Pendiente** — usuario sin campo cargo/nombre titular |
| `{{ valido_nombre_cargo }}` | Nombre y cargo del titular | — | **Pendiente** — usuario sin campo cargo/nombre titular |

## Endpoint

```
POST /api/programas/actividades/{actividad_id}/mes/{mes}/formato-evidencia
Body: {
  "justificacion_tecnica": "...",
  "evidencias": [
    {
      "evidencia_id": 1,
      "tipo_documento": "Acta de entrega-recepción",
      "folios_referencias": "OF-123 / 2026-01-15"
    }
  ]
}
Response: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

## Campos de BD sugeridos para iteraciones futuras

- `CatalogoProgramas` o catálogo PMD: eje estratégico del PMD
- `Actividades`: unidad de medida del indicador
- `ProgramacionEvidencia`: persistir tipo de documento y folios/referencias en BD (actualmente solo en payload del reporte)
- `Usuario` o perfil de capturista: nombre completo y cargo para firmas
