import re
from collections import defaultdict
from typing import Any

from app.models.actividades import Actividades
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.programacion_avance import StatusAvance

MESES_NOMBRES_CORTOS = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}

MESES_NOMBRES_LARGOS = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def natural_sort_key(value: str) -> list[Any]:
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", value)
    ]


def sort_by_natural_clave(items: list, clave_attr: str = "clave") -> list:
    return sorted(items, key=lambda item: natural_sort_key(getattr(item, clave_attr) or ""))


def get_linea_accion_pmd(actividad: Actividades) -> str:
    if actividad.lineas_pmd:
        return ", ".join(pmd.clave for pmd in actividad.lineas_pmd)
    return "N/A"


def get_unidad_clave(actividad: Actividades) -> str:
    if (
        actividad.componente
        and actividad.componente.programa
        and actividad.componente.programa.unidad_administrativa
    ):
        return actividad.componente.programa.unidad_administrativa.clave
    return ""


def build_evidencias_list(avance) -> list[dict]:
    return [
        {
            "id": ev.id,
            "nombre_original": ev.nombre_original,
            "url_archivo": ev.url_archivo,
            "mime_type": ev.mime_type,
        }
        for ev in avance.evidencias
        if ev.activo
    ]


def build_programacion_mensual(actividad: Actividades) -> list[dict]:
    metas_dict = {meta.mes: meta for meta in actividad.metas_mensuales}
    programacion_mensual = []

    for num_mes in range(1, 13):
        nombre_mes = MESES_NOMBRES_CORTOS[num_mes]
        meta_record = metas_dict.get(num_mes)

        estado = "en_revision"
        avance_meta = 0
        status_val = "BORRADOR"
        comentarios_val = None
        evidencias_val: list[dict] = []
        fecha_envio_val = None
        fecha_revision_val = None

        if meta_record:
            avance = meta_record.avance
            if avance:
                avance_meta = avance.avance_meta
                status_val = avance.status.value if avance.status else "BORRADOR"
                comentarios_val = avance.comentarios_revision
                fecha_envio_val = avance.fecha_envio
                fecha_revision_val = avance.fecha_revision
                evidencias_val = build_evidencias_list(avance)
                if avance.status == StatusAvance.FINALIZADO:
                    estado = "finalizado"

        programacion_mensual.append(
            {
                "mes": nombre_mes,
                "mesNumero": num_mes,
                "meta": meta_record.cantidad_programada if meta_record else 0,
                "estado": estado,
                "avanceMeta": avance_meta,
                "status": status_val,
                "evidencias": evidencias_val,
                "comentarios": comentarios_val,
                "fechaEnvio": fecha_envio_val,
                "fechaRevision": fecha_revision_val,
            }
        )

    return programacion_mensual


def build_actividad_out(actividad: Actividades, programa_clave: str | None = None) -> dict:
    if programa_clave is None:
        if actividad.componente and actividad.componente.programa:
            programa_clave = actividad.componente.programa.clave
        else:
            programa_clave = ""

    return {
        "id": actividad.id,
        "programaClave": programa_clave,
        "componenteClave": actividad.componente.clave if actividad.componente else "",
        "clave": actividad.clave,
        "descripcion": actividad.descripcion,
        "metaAnual": actividad.meta,
        "costoEstimado": float(actividad.monto or 0),
        "unidadAdministrativaClave": get_unidad_clave(actividad),
        "lineaAccionPmd": get_linea_accion_pmd(actividad),
        "programacionMensual": build_programacion_mensual(actividad),
    }


def build_actividades_out(
    actividades: list[Actividades],
    programa_clave: str | None = None,
) -> list[dict]:
    return [
        build_actividad_out(
            actividad,
            programa_clave=programa_clave or (
                actividad.componente.programa.clave
                if actividad.componente and actividad.componente.programa
                else ""
            ),
        )
        for actividad in sort_by_natural_clave(actividades)
    ]


def aggregate_programas_grouped(
    programas: list[CatalogoProgramas],
    presupuesto_fn,
) -> list[dict]:
    programas_grouped: dict[str, list[CatalogoProgramas]] = defaultdict(list)
    for programa in programas:
        programas_grouped[programa.clave].append(programa)

    result = []
    for clave in sorted(programas_grouped.keys(), key=natural_sort_key):
        group = programas_grouped[clave]
        result.append(build_programa_out_from_group(group, presupuesto_fn))
    return result


def build_programa_out_from_group(
    programas: list[CatalogoProgramas],
    presupuesto_fn,
) -> dict:
    p0 = programas[0]

    units = []
    seen_units: set[int] = set()
    for programa in programas:
        if (
            programa.unidad_administrativa
            and programa.unidad_administrativa.id not in seen_units
        ):
            units.append(programa.unidad_administrativa)
            seen_units.add(programa.unidad_administrativa.id)

    ejecutor_clave = ", ".join(unit.clave for unit in units)
    ejecutor_nombre = ", ".join(unit.nombre for unit in units)

    total_presupuesto_asignado = 0.0
    total_fiscales = 0.0
    total_participaciones = 0.0
    total_faismun = 0.0
    total_fortamun = 0.0
    total_otros = 0.0

    for programa in programas:
        pres = presupuesto_fn(programa.unidad_administrativa_id, programa.ejercicio_id)
        total_presupuesto_asignado += pres["presupuestoAsignado"]
        total_fiscales += pres["presupuesto"]["recursosFiscales"]
        total_participaciones += pres["presupuesto"]["participaciones"]
        total_faismun += pres["presupuesto"]["faismun"]
        total_fortamun += pres["presupuesto"]["fortamun"]
        total_otros += pres["presupuesto"]["otros"]

    return {
        "id": p0.id,
        "clave": p0.clave,
        "descripcion": p0.programa,
        "ejecutorClave": ejecutor_clave,
        "ejecutorNombre": ejecutor_nombre,
        "ejercicio": p0.ejercicio.anio if p0.ejercicio else 0,
        "fechaCreacion": p0.creado_en.isoformat() if p0.creado_en else "",
        "ultimaActualizacion": p0.actualizado_en.isoformat() if p0.actualizado_en else None,
        "presupuestoAsignado": total_presupuesto_asignado,
        "presupuesto": {
            "recursosFiscales": total_fiscales,
            "participaciones": total_participaciones,
            "faismun": total_faismun,
            "fortamun": total_fortamun,
            "otros": total_otros,
        },
        "estadoFlujo": p0.estado_flujo or "configuracion",
    }


def build_componentes_out(componentes: list[Componentes], programa_clave: str) -> list[dict]:
    return [
        {
            "id": componente.id,
            "programaClave": programa_clave,
            "clave": componente.clave,
            "descripcion": componente.descripcion,
        }
        for componente in sort_by_natural_clave(componentes)
    ]
