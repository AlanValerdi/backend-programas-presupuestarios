from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import re
from collections import defaultdict


def safe_int(value, default=0):
    if value is None:
        return default
    s = str(value).strip()
    if s == "" or s.lower() == "nan":
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default

from app.api.dependencies import get_db, get_entidad_from_slug, require_any_role, TokenData
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.models.catalogo_fuentes_financiamiento import CatalogoFuentesFinanciamiento
from app.models.inter_techo_financiero import TechoFinanciero
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.actividades import Actividades
from app.models.programacion_meta import ProgramacionMeta
from app.models.catalogo_pmd import CatalogoPMD
from app.models.inter_actividades_pmd import ActividadPMD
from app.models.entidad import Entidad

router = APIRouter(prefix="/etl", tags=["etl"])


@router.post("/poblar_unidades_administrativas")
def poblar_unidades_administrativas(
    file: UploadFile = File(...),
    ejercicio_id: int = Form(...),
    confirmar_actualizacion: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_any_role()),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo archivos Excel (.xlsx, .xls)")

    try:
        df = pd.read_excel(file.file, sheet_name="Unidades", skiprows=4)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer la hoja 'Unidades': {str(e)}")

    df = df.dropna(how="all").reset_index(drop=True)

    headers = df.columns.tolist()
    posibles_claves = [c for c in headers if "número" in c.lower() or "numero" in c.lower() or "num" in c.lower()]
    if not posibles_claves:
        raise HTTPException(status_code=400, detail="No se encontró columna 'Número' en el Excel")

    col_numero = posibles_claves[0]
    col_nombre = next((c for c in headers if "nombre" in c.lower()), None)
    col_plazas = next((c for c in headers if "plaza" in c.lower()), None)

    fuente_cols = {}
    for col in headers:
        col_str = str(col).strip()
        match = re.match(r"^(\d+(?:\.\d+)*)", col_str)
        if match:
            clave_fuente = match.group(1)
            fuente_cols[clave_fuente] = col

    unidad_clave_idx = col_numero
    unidad_nombre_idx = col_nombre
    unidad_plazas_idx = col_plazas

    db_unidades = {
        u.clave: u
        for u in db.query(CatalogoUnidadesAdministrativas)
        .filter(CatalogoUnidadesAdministrativas.entidad_id == entidad.id)
        .all()
    }
    db_techos = db.query(TechoFinanciero).filter(TechoFinanciero.ejercicio_id == ejercicio_id).all()
    db_techos_map = defaultdict(list)
    for t in db_techos:
        db_techos_map[(t.unidad_administrativa_id, t.fuente_financiamiento_id)].append(t)

    db_fuentes = {
        f.clave: f
        for f in db.query(CatalogoFuentesFinanciamiento)
        .filter(CatalogoFuentesFinanciamiento.entidad_id == entidad.id)
        .all()
    }
    for clave_fuente, col in fuente_cols.items():
        descripcion_fuente = str(col).strip()
        if clave_fuente not in db_fuentes:
            nueva = CatalogoFuentesFinanciamiento(
                clave=clave_fuente,
                descripcion=descripcion_fuente,
                entidad_id=entidad.id,
            )
            db.add(nueva)
            db.flush()
            db_fuentes[clave_fuente] = nueva

    nuevos_unidades = []
    modificados_unidades = []
    nuevos_techos = []
    modificados_techos = []
    errores = []

    for _, row in df.iterrows():
        clave = str(row[unidad_clave_idx]).strip() if pd.notna(row[unidad_clave_idx]) else None
        if not clave or clave == "" or clave == "nan":
            continue

        plazas_val = safe_int(row[unidad_plazas_idx]) if unidad_plazas_idx and pd.notna(row[unidad_plazas_idx]) else 0
        nombre_val = str(row[unidad_nombre_idx]).strip() if unidad_nombre_idx and pd.notna(row[unidad_nombre_idx]) else ""

        if clave in db_unidades:
            u = db_unidades[clave]
            cambios = []
            if u.plazas != plazas_val:
                cambios.append(f"plazas: {u.plazas} -> {plazas_val}")
                u.plazas = plazas_val
            if nombre_val and u.nombre != nombre_val:
                cambios.append(f"nombre: {u.nombre} -> {nombre_val}")
                u.nombre = nombre_val
            if cambios:
                modificados_unidades.append({"clave": clave, "cambios": cambios})
        else:
            nueva = CatalogoUnidadesAdministrativas(
                clave=clave,
                plazas=plazas_val,
                nombre=nombre_val,
                entidad_id=entidad.id,
            )
            db.add(nueva)
            db.flush()
            db_unidades[clave] = nueva
            nuevos_unidades.append({"clave": clave, "plazas": plazas_val, "nombre": nombre_val})

        unidad_id = db_unidades[clave].id
        for clave_fuente, col_fuente in fuente_cols.items():
            monto_raw = row[col_fuente]
            monto_val = 0.0
            if pd.notna(monto_raw):
                try:
                    monto_val = float(monto_raw)
                except (ValueError, TypeError):
                    monto_val = 0.0

            fuente_obj = db_fuentes.get(clave_fuente)
            if not fuente_obj:
                continue

            key = (unidad_id, fuente_obj.id)
            techos_existentes = db_techos_map.get(key, [])
            if techos_existentes:
                t = techos_existentes[0]
                if float(t.monto or 0) != monto_val:
                    modificados_techos.append({
                        "unidad": clave,
                        "fuente": clave_fuente,
                        "monto_anterior": float(t.monto or 0),
                        "monto_nuevo": monto_val
                    })
                    t.monto = monto_val
            else:
                nuevos_techos.append({
                    "unidad": clave,
                    "fuente": clave_fuente,
                    "monto": monto_val
                })
                nuevo_techo = TechoFinanciero(
                    ejercicio_id=ejercicio_id,
                    unidad_administrativa_id=unidad_id,
                    fuente_financiamiento_id=fuente_obj.id,
                    monto=monto_val
                )
                db.add(nuevo_techo)

    if confirmar_actualizacion:
        db.commit()
        return {
            "status": "confirmado",
            "nuevas_unidades": nuevos_unidades,
            "unidades_modificadas": modificados_unidades,
            "nuevos_techos": nuevos_techos,
            "techos_modificados": modificados_techos,
            "errores": errores
        }

    return {
        "status": "dry_run",
        "nuevas_unidades": nuevos_unidades,
        "unidades_modificadas": modificados_unidades,
        "nuevos_techos": nuevos_techos,
        "techos_modificados": modificados_techos,
        "errores": errores
    }


@router.post("/poblar_matriz_programatica")
def poblar_matriz_programatica(
    file: UploadFile = File(...),
    ejercicio_id: int = Form(...),
    confirmar_actualizacion: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_any_role()),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo archivos Excel (.xlsx, .xls)")

    try:
        # TODO: Implementar autodeteccion de fila de encabezado
        # Buscar la primera fila que contenga 'CLAVE', 'PROGRAMA', 'EJECUTOR'
        df = pd.read_excel(file.file, sheet_name="Componentes y actividades", header=3)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer la hoja 'Componentes y actividades': {str(e)}")

    df = df.dropna(how="all").reset_index(drop=True)

    col_map = {
        "programa_clave": None,
        "programa_nombre": None,
        "programa_monto": None,
        "ejecutor_clave": None,
        "ejecutor_nombre": None,
        "componente_clave": None,
        "componente_descripcion": None,
        "componente_monto": None,
        "actividad_clave": None,
        "actividad_descripcion": None,
        "actividad_monto": None,
        "actividad_meta": None,
        "pmd_linea": None,
    }
    for col in df.columns:
        col_str = str(col).strip()
        if col_str == "CLAVE":
            col_map["programa_clave"] = col
        elif col_str == "PROGRAMA":
            col_map["programa_nombre"] = col
        elif col_str == "MONTO":
            col_map["programa_monto"] = col
        elif col_str == "CLAVE.1":
            col_map["ejecutor_clave"] = col
        elif col_str == "NOMBRE":
            col_map["ejecutor_nombre"] = col
        elif col_str == "CLAVE.2":
            col_map["componente_clave"] = col
        elif col_str == "DESCRIPCION":
            col_map["componente_descripcion"] = col
        elif col_str == "MONTO.1":
            col_map["componente_monto"] = col
        elif col_str == "MONTO.2":
            col_map["actividad_monto"] = col
        elif col_str == "CLAVE.3":
            col_map["actividad_clave"] = col
        elif col_str == "DESCRIPCION.1":
            col_map["actividad_descripcion"] = col
        elif col_str == "LINEA DE ACCION PMD":
            col_map["pmd_linea"] = col
        elif col_str == "Unnamed: 15":
            col_map["actividad_meta"] = col

    missing = [k for k, v in col_map.items() if v is None]
    if col_map["programa_clave"] is None or col_map["programa_nombre"] is None:
        raise HTTPException(
            status_code=400,
            detail=f"No se encontraron columnas 'CLAVE' o 'PROGRAMA'. Columnas detectadas: {list(df.columns)}. Faltantes: {missing}"
        )

    cols_ffill = []
    for key in ["programa_clave", "programa_nombre", "programa_monto", "ejecutor_clave", "ejecutor_nombre", "componente_clave", "componente_descripcion", "componente_monto"]:
        if col_map[key]:
            cols_ffill.append(col_map[key])
    df[cols_ffill] = df[cols_ffill].ffill()

    db_programas = {
        (p.clave, p.unidad_administrativa_id): p
        for p in db.query(CatalogoProgramas)
        .filter(
            CatalogoProgramas.ejercicio_id == ejercicio_id,
            CatalogoProgramas.entidad_id == entidad.id,
        )
        .all()
    }
    db_componentes = {(c.clave, c.programa_id): c for c in db.query(Componentes).all()}
    db_actividades = {a.clave: a for a in db.query(Actividades).all()}
    db_pmd = {
        p.clave: p
        for p in db.query(CatalogoPMD).filter(CatalogoPMD.entidad_id == entidad.id).all()
    }

    db_unidades = {
        u.clave: u
        for u in db.query(CatalogoUnidadesAdministrativas)
        .filter(CatalogoUnidadesAdministrativas.entidad_id == entidad.id)
        .all()
    }

    nuevos_programas = []
    modificados_programas = []
    nuevos_componentes = []
    modificados_componentes = []
    nuevos_actividades = []
    modificados_actividades = []
    nuevas_metas = []
    modificadas_metas = []
    nuevos_pmd = []
    nuevas_relaciones_pmd = []
    errores = []

    programa_actual = None
    componente_actual = None
    actividad_actual = None

    mes_columns = []
    for i, col in enumerate(df.columns):
        col_str = str(col).strip()
        if col_str.startswith("Cantidad"):
            mes_columns.append(col)
    mes_columns = sorted(mes_columns, key=lambda c: list(df.columns).index(c))

    for _, row in df.iterrows():
        prog_clave = str(row[col_map["programa_clave"]]).strip() if pd.notna(row[col_map["programa_clave"]]) else None
        prog_nombre = str(row[col_map["programa_nombre"]]).strip() if pd.notna(row[col_map["programa_nombre"]]) else None
        prog_monto_raw = row[col_map["programa_monto"]] if col_map["programa_monto"] else None

        ejecutor_clave_raw = str(row[col_map["ejecutor_clave"]]).strip() if col_map["ejecutor_clave"] and pd.notna(row[col_map["ejecutor_clave"]]) else None
        ejecutor_nombre_raw = str(row[col_map["ejecutor_nombre"]]).strip() if col_map["ejecutor_nombre"] and pd.notna(row[col_map["ejecutor_nombre"]]) else None

        comp_clave = str(row[col_map["componente_clave"]]).strip() if col_map["componente_clave"] and pd.notna(row[col_map["componente_clave"]]) else None
        comp_desc = str(row[col_map["componente_descripcion"]]).strip() if col_map["componente_descripcion"] and pd.notna(row[col_map["componente_descripcion"]]) else ""
        comp_monto_raw = row[col_map["componente_monto"]] if col_map["componente_monto"] else None

        act_clave = str(row[col_map["actividad_clave"]]).strip() if col_map["actividad_clave"] and pd.notna(row[col_map["actividad_clave"]]) else None
        act_desc = str(row[col_map["actividad_descripcion"]]).strip() if col_map["actividad_descripcion"] and pd.notna(row[col_map["actividad_descripcion"]]) else ""
        act_monto_raw = row[col_map["actividad_monto"]] if col_map["actividad_monto"] else None
        act_meta_raw = row[col_map["actividad_meta"]] if col_map["actividad_meta"] else None
        pmd_linea_raw = row[col_map["pmd_linea"]] if col_map["pmd_linea"] else None

        es_fila_vacia = (
            not prog_clave and not comp_clave and not act_clave
        )
        if es_fila_vacia:
            continue

        if prog_nombre and prog_nombre.lower() in ("total", "diferencia", "subtotal"):
            continue

        if prog_nombre and "ley de ingresos" in prog_nombre.lower():
            continue

        ejecutor_clave = ejecutor_clave_raw.split()[0] if ejecutor_clave_raw else None
        ejecutor_nombre = " ".join(ejecutor_clave_raw.split()[1:]) if ejecutor_clave_raw and len(ejecutor_clave_raw.split()) > 1 else (ejecutor_clave_raw or None)

        if ejecutor_clave and ejecutor_clave not in db_unidades:
            nueva_u = CatalogoUnidadesAdministrativas(
                clave=ejecutor_clave,
                plazas=None,
                nombre=ejecutor_nombre,
                entidad_id=entidad.id,
            )
            db.add(nueva_u)
            db.flush()
            db_unidades[ejecutor_clave] = nueva_u

        unidad_ejecutora = db_unidades.get(ejecutor_clave) if ejecutor_clave else None

        if prog_clave and prog_clave not in ("", "nan", "None") and prog_nombre:
            prog_key = (prog_clave, unidad_ejecutora.id if unidad_ejecutora else None)
            if prog_key not in db_programas:
                nuevo_p = CatalogoProgramas(
                    clave=prog_clave,
                    programa=prog_nombre,
                    entidad_id=entidad.id,
                    ejercicio_id=ejercicio_id,
                    unidad_administrativa_id=unidad_ejecutora.id if unidad_ejecutora else None,
                    campos_extra={},
                )
                db.add(nuevo_p)
                db.flush()
                db_programas[prog_key] = nuevo_p
                nuevos_programas.append({"clave": prog_clave, "programa": prog_nombre})
                programa_actual = nuevo_p
            else:
                p = db_programas[prog_key]
                if p.programa != prog_nombre:
                    modificados_programas.append({"clave": prog_clave, "cambios": [f"programa: {p.programa} -> {prog_nombre}"]})
                    p.programa = prog_nombre
                programa_actual = p

        if comp_clave and comp_clave not in ("", "nan", "None") and programa_actual:
            comp_monto = 0.0
            if pd.notna(comp_monto_raw):
                try:
                    comp_monto = float(comp_monto_raw)
                except (ValueError, TypeError):
                    comp_monto = 0.0

            comp_key = (comp_clave, programa_actual.id)
            if comp_key not in db_componentes:
                nuevo_c = Componentes(
                    clave=comp_clave,
                    descripcion=comp_desc,
                    programa_id=programa_actual.id,
                )
                db.add(nuevo_c)
                db.flush()
                db_componentes[comp_key] = nuevo_c
                nuevos_componentes.append({"clave": comp_clave, "descripcion": comp_desc})
                componente_actual = nuevo_c
            else:
                c = db_componentes[comp_key]
                if comp_desc and c.descripcion != comp_desc:
                    modificados_componentes.append({"clave": comp_clave, "cambios": [f"descripcion: {c.descripcion} -> {comp_desc}"]})
                    c.descripcion = comp_desc
                componente_actual = c

        if act_clave and act_clave not in ("", "nan", "None") and componente_actual:
            act_monto = 0.0
            if pd.notna(act_monto_raw):
                try:
                    act_monto = float(act_monto_raw)
                except (ValueError, TypeError):
                    act_monto = 0.0

            act_meta = 0
            if pd.notna(act_meta_raw):
                try:
                    act_meta = int(float(act_meta_raw))
                except (ValueError, TypeError):
                    act_meta = 0

            pmd_claves_raw = []
            if pd.notna(pmd_linea_raw):
                for parte in str(pmd_linea_raw).split("\n"):
                    clave_pmd = parte.strip().rstrip(".")
                    if clave_pmd:
                        pmd_claves_raw.append(clave_pmd)

            actividad_existente = next((a for a in db.query(Actividades).filter(
                Actividades.clave == act_clave,
                Actividades.componente_id == componente_actual.id
            ).all()), None)

            if not actividad_existente:
                nueva_a = Actividades(
                    clave=act_clave,
                    descripcion=act_desc,
                    monto=act_monto,
                    meta=act_meta,
                    componente_id=componente_actual.id
                )
                db.add(nueva_a)
                db.flush()
                db_actividades[act_clave] = nueva_a
                actividad_existente = nueva_a
                nuevos_actividades.append({"clave": act_clave, "descripcion": act_desc, "meta": act_meta})
            else:
                cambios = []
                if act_desc and actividad_existente.descripcion != act_desc:
                    cambios.append(f"descripcion: {actividad_existente.descripcion} -> {act_desc}")
                    actividad_existente.descripcion = act_desc
                if actividad_existente.meta != act_meta:
                    cambios.append(f"meta: {actividad_existente.meta} -> {act_meta}")
                    actividad_existente.meta = act_meta
                if cambios:
                    modificados_actividades.append({"clave": act_clave, "cambios": cambios})

            for clave_pmd in pmd_claves_raw:
                if clave_pmd not in db_pmd:
                    nuevo_pmd = CatalogoPMD(clave=clave_pmd, entidad_id=entidad.id)
                    db.add(nuevo_pmd)
                    db.flush()
                    db_pmd[clave_pmd] = nuevo_pmd
                    nuevos_pmd.append({"clave": clave_pmd})

                pmd_obj = db_pmd[clave_pmd]
                existe_rel = db.query(ActividadPMD).filter(
                    ActividadPMD.actividad_id == actividad_existente.id,
                    ActividadPMD.pmd_id == pmd_obj.id
                ).first()
                if not existe_rel:
                    nueva_rel = ActividadPMD(actividad_id=actividad_existente.id, pmd_id=pmd_obj.id)
                    db.add(nueva_rel)
                    nuevas_relaciones_pmd.append({"actividad": act_clave, "pmd": clave_pmd})

            actividad_actual = actividad_existente

            if mes_columns and actividad_actual:
                for mes_idx, col in enumerate(mes_columns, start=1):
                    meta_mes_raw = row[col]
                    meta_mes_val = 0
                    if pd.notna(meta_mes_raw):
                        try:
                            meta_mes_val = int(float(meta_mes_raw))
                        except (ValueError, TypeError):
                            meta_mes_val = 0

                    meta_existente = db.query(ProgramacionMeta).filter(
                        ProgramacionMeta.actividad_id == actividad_actual.id,
                        ProgramacionMeta.mes == mes_idx
                    ).first()

                    if not meta_existente:
                        nueva_meta = ProgramacionMeta(
                            cantidad_programada=meta_mes_val,
                            mes=mes_idx,
                            actividad_id=actividad_actual.id
                        )
                        db.add(nueva_meta)
                        nuevas_metas.append({"actividad": act_clave, "mes": mes_idx, "cantidad": meta_mes_val})
                    elif meta_existente.cantidad_programada != meta_mes_val:
                        modificadas_metas.append({
                            "actividad": act_clave,
                            "mes": mes_idx,
                            "anterior": meta_existente.cantidad_programada,
                            "nuevo": meta_mes_val
                        })
                        meta_existente.cantidad_programada = meta_mes_val

    if confirmar_actualizacion:
        db.commit()
        return {
            "status": "confirmado",
            "nuevos_programas": nuevos_programas,
            "programas_modificados": modificados_programas,
            "nuevos_componentes": nuevos_componentes,
            "componentes_modificados": modificados_componentes,
            "nuevas_actividades": nuevos_actividades,
            "actividades_modificadas": modificados_actividades,
            "nuevos_pmd": nuevos_pmd,
            "nuevas_relaciones_pmd": nuevas_relaciones_pmd,
            "nuevas_metas": nuevas_metas,
            "metas_modificadas": modificadas_metas,
            "errores": errores
        }

    return {
        "status": "dry_run",
        "nuevos_programas": nuevos_programas,
        "programas_modificados": modificados_programas,
        "nuevos_componentes": nuevos_componentes,
        "componentes_modificados": modificados_componentes,
        "nuevas_actividades": nuevos_actividades,
        "actividades_modificadas": modificados_actividades,
        "nuevos_pmd": nuevos_pmd,
        "nuevas_relaciones_pmd": nuevas_relaciones_pmd,
        "nuevas_metas": nuevas_metas,
        "metas_modificadas": modificadas_metas,
        "errores": errores
    }
