from __future__ import annotations

import io
from pathlib import Path

from docxtpl import DocxTemplate
from sqlalchemy.orm import Session

from app.crud.programas import actividades as actividades_crud
from app.crud.programas import avances as avances_crud
from app.models.actividades import Actividades
from app.models.programacion_meta import ProgramacionMeta
from app.schemas.programas.inputs import EvidenciaDocumentalInput

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "Formato de Evidencia - Cumplimiento de Metas - Copy.docx"
)

TRIMESTRE_ORDINAL = {
    1: "1er",
    2: "2do",
    3: "3er",
    4: "4to",
}


def _trimestre_from_mes(mes: int) -> int:
    return ((mes - 1) // 3) + 1


def _format_trimestre_reporte(mes: int, anio: int) -> str:
    trimestre = _trimestre_from_mes(mes)
    ordinal = TRIMESTRE_ORDINAL[trimestre]
    return f"{ordinal} Trimestre del Ejercicio Fiscal {anio}"


def _format_porcentaje_cumplimiento(programada: int, alcanzada: int) -> str:
    if programada == 0:
        return f"({alcanzada} / {programada}) * 100 = N/A"
    porcentaje = (alcanzada / programada) * 100
    return f"({alcanzada} / {programada}) * 100 = {porcentaje:.2f}%"


def _build_evidencia_download_url(base_url: str, evidencia_id: int) -> str:
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/api/programas/evidencia/download/{evidencia_id}"


def build_evidencias_documentales(
    meta_record: ProgramacionMeta | None,
    evidencias_input: list[EvidenciaDocumentalInput],
    base_url: str,
) -> list[dict[str, str]]:
    metadata_by_id = {
        item.evidencia_id: item for item in evidencias_input
    }
    result: list[dict[str, str]] = []

    if not meta_record or not meta_record.avance:
        return result

    for evidencia in meta_record.avance.evidencias:
        if not evidencia.activo:
            continue

        metadata = metadata_by_id.get(evidencia.id)
        result.append(
            {
                "tipo_documento": (
                    metadata.tipo_documento.strip() if metadata else ""
                ),
                "folios_referencias": (
                    metadata.folios_referencias.strip() if metadata else ""
                ),
                "ubicacion_archivo": _build_evidencia_download_url(
                    base_url,
                    evidencia.id,
                ),
                "nombre_archivo": evidencia.nombre_original,
            }
        )

    return result


def build_formato_evidencia_context(
    actividad: Actividades,
    mes: int,
    justificacion_tecnica: str = "",
    evidencias_input: list[EvidenciaDocumentalInput] | None = None,
    base_url: str = "",
    meta_record: ProgramacionMeta | None = None,
) -> dict:
    programa = actividad.componente.programa if actividad.componente else None
    unidad = programa.unidad_administrativa if programa else None
    ejercicio_anio = programa.ejercicio.anio if programa and programa.ejercicio else 0

    if meta_record is None:
        meta_record = next(
            (meta for meta in actividad.metas_mensuales if meta.mes == mes),
            None,
        )

    meta_programada = meta_record.cantidad_programada if meta_record else 0
    meta_alcanzada = 0
    if meta_record and meta_record.avance:
        meta_alcanzada = meta_record.avance.avance_meta or 0

    evidencias_documentales = build_evidencias_documentales(
        meta_record,
        evidencias_input or [],
        base_url,
    )

    return {
        "dependencia_responsable": unidad.nombre if unidad else "",
        "programa_presupuestario": (
            f"{programa.clave} - {programa.programa}" if programa else ""
        ),
        "eje_pmd": "",
        "trimestre_reporte": _format_trimestre_reporte(mes, ejercicio_anio),
        "nivel_mir": "Actividad",
        "nombre_indicador": actividad.descripcion or "",
        "unidad_medida": "",
        "meta_programada_periodo": str(meta_programada),
        "meta_alcanzada": str(meta_alcanzada),
        "porcentaje_cumplimiento": _format_porcentaje_cumplimiento(
            meta_programada,
            meta_alcanzada,
        ),
        "evidencias_documentales": evidencias_documentales,
        "justificacion_tecnica": justificacion_tecnica.strip(),
        "elaboro_nombre_cargo": "",
        "valido_nombre_cargo": "",
    }


def render_formato_evidencia(
    actividad: Actividades,
    mes: int,
    justificacion_tecnica: str = "",
    evidencias_input: list[EvidenciaDocumentalInput] | None = None,
    base_url: str = "",
    meta_record: ProgramacionMeta | None = None,
) -> io.BytesIO:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Plantilla no encontrada: {TEMPLATE_PATH}")

    context = build_formato_evidencia_context(
        actividad,
        mes,
        justificacion_tecnica=justificacion_tecnica,
        evidencias_input=evidencias_input,
        base_url=base_url,
        meta_record=meta_record,
    )
    doc = DocxTemplate(str(TEMPLATE_PATH))
    doc.render(context)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output


def generate_formato_evidencia_document(
    db: Session,
    actividad_id: int,
    mes: int,
    justificacion_tecnica: str = "",
    evidencias_input: list[EvidenciaDocumentalInput] | None = None,
    base_url: str = "",
) -> tuple[io.BytesIO, str]:
    actividad = actividades_crud.get_actividad_by_id(db, actividad_id)
    if not actividad:
        raise ValueError("Actividad no encontrada")

    if mes < 1 or mes > 12:
        raise ValueError("Mes inválido")

    meta = avances_crud.get_programacion_meta(db, actividad_id, mes)
    if not meta:
        raise ValueError("Programación mensual no encontrada")

    document = render_formato_evidencia(
        actividad,
        mes,
        justificacion_tecnica=justificacion_tecnica,
        evidencias_input=evidencias_input,
        base_url=base_url,
        meta_record=meta,
    )
    filename = (
        f"Formato_Evidencia_{actividad.clave.replace('.', '_')}_mes{mes}.docx"
    )
    return document, filename
