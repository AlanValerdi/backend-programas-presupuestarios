from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import datetime
from app.api.dependencies import get_db, get_current_user, TokenData
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.actividades import Actividades
from app.models.usuario import RolUsuario
from app.models.inter_techo_financiero import TechoFinanciero
from app.models.programacion_avance import StatusAvance, ProgramacionAvance
from app.models.programacion_meta import ProgramacionMeta
from app.models.programacion_evidencia import ProgramacionEvidencia
from app.models.captura_periodos import CapturaPeriodos
from app.models.ejercicio import Ejercicio
from app.schemas.programas import ProgramaOut, ComponenteOut, ActividadOut


router = APIRouter(prefix="/api/programas", tags=["programas"])


def obtener_presupuesto_programa(db: Session, unidad_id: int, ejercicio_id: int):
    techos = (
        db.query(TechoFinanciero)
        .filter(
            TechoFinanciero.unidad_administrativa_id == unidad_id,
            TechoFinanciero.ejercicio_id == ejercicio_id
        )
        .all()
    )

    recursos_fiscales = 0.0
    participaciones = 0.0
    faismun = 0.0
    fortamun = 0.0
    otros = 0.0

    for t in techos:
        monto = float(t.monto or 0.0)
        clave = t.fuente_financiamiento.clave if t.fuente_financiamiento else ""
        if clave == "1.01":
            recursos_fiscales += monto
        elif clave == "5.01":
            participaciones += monto
        elif clave == "5.02":
            faismun += monto
        elif clave == "5.3":
            fortamun += monto
        else:
            otros += monto

    total = recursos_fiscales + participaciones + faismun + fortamun + otros

    return {
        "presupuestoAsignado": total,
        "presupuesto": {
            "recursosFiscales": recursos_fiscales,
            "participaciones": participaciones,
            "faismun": faismun,
            "fortamun": fortamun,
            "otros": otros
        }
    }


@router.get("", response_model=list[ProgramaOut])
def listar_programas(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(CatalogoProgramas)

    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )

    programas = query.order_by(CatalogoProgramas.clave).all()
    
    from collections import defaultdict
    programas_grouped = defaultdict(list)
    for p in programas:
        programas_grouped[p.clave].append(p)
        
    res = []
    for clave in sorted(programas_grouped.keys()):
        group = programas_grouped[clave]
        p0 = group[0]
        
        # Aggregate executors
        units = []
        seen_units = set()
        for p in group:
            if p.unidad_administrativa and p.unidad_administrativa.id not in seen_units:
                units.append(p.unidad_administrativa)
                seen_units.add(p.unidad_administrativa.id)
                
        ejecutorClave = ", ".join([u.clave for u in units])
        ejecutorNombre = ", ".join([u.nombre for u in units])
        
        # Aggregate budgets
        total_presupuesto_asignado = 0.0
        total_fiscales = 0.0
        total_participaciones = 0.0
        total_faismun = 0.0
        total_fortamun = 0.0
        total_otros = 0.0
        
        for p in group:
            pres = obtener_presupuesto_programa(db, p.unidad_administrativa_id, p.ejercicio_id)
            total_presupuesto_asignado += pres["presupuestoAsignado"]
            total_fiscales += pres["presupuesto"]["recursosFiscales"]
            total_participaciones += pres["presupuesto"]["participaciones"]
            total_faismun += pres["presupuesto"]["faismun"]
            total_fortamun += pres["presupuesto"]["fortamun"]
            total_otros += pres["presupuesto"]["otros"]
            
        res.append({
            "id": p0.id,
            "clave": p0.clave,
            "descripcion": p0.programa,
            "ejecutorClave": ejecutorClave,
            "ejecutorNombre": ejecutorNombre,
            "ejercicio": p0.ejercicio.anio if p0.ejercicio else 0,
            "fechaCreacion": p0.creado_en.isoformat() if p0.creado_en else "",
            "ultimaActualizacion": p0.actualizado_en.isoformat() if p0.actualizado_en else None,
            "presupuestoAsignado": total_presupuesto_asignado,
            "presupuesto": {
                "recursosFiscales": total_fiscales,
                "participaciones": total_participaciones,
                "faismun": total_faismun,
                "fortamun": total_fortamun,
                "otros": total_otros
            },
            "estadoFlujo": p0.estado_flujo or "configuracion"
        })
    return res


@router.get("/config/settings")
def obtener_settings(db: Session = Depends(get_db)):
    ejercicio = db.query(Ejercicio).filter(Ejercicio.activo == True).first()
    if not ejercicio:
        return {"mostrar_montos": True}
    return {"mostrar_montos": ejercicio.mostrar_montos}


@router.put("/config/settings")
def actualizar_settings(
    mostrar_montos: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes.")

    ejercicio = db.query(Ejercicio).filter(Ejercicio.activo == True).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio activo no encontrado")

    ejercicio.mostrar_montos = mostrar_montos
    db.commit()
    return {"mostrar_montos": ejercicio.mostrar_montos}


@router.get("/{clave}", response_model=ProgramaOut)
def obtener_programa(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave)
    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )
    programas = query.all()
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    p0 = programas[0]
    
    # Aggregate executors
    units = []
    seen_units = set()
    for p in programas:
        if p.unidad_administrativa and p.unidad_administrativa.id not in seen_units:
            units.append(p.unidad_administrativa)
            seen_units.add(p.unidad_administrativa.id)
            
    ejecutorClave = ", ".join([u.clave for u in units])
    ejecutorNombre = ", ".join([u.nombre for u in units])
    
    # Aggregate budgets
    total_presupuesto_asignado = 0.0
    total_fiscales = 0.0
    total_participaciones = 0.0
    total_faismun = 0.0
    total_fortamun = 0.0
    total_otros = 0.0
    
    for p in programas:
        pres = obtener_presupuesto_programa(db, p.unidad_administrativa_id, p.ejercicio_id)
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
        "ejecutorClave": ejecutorClave,
        "ejecutorNombre": ejecutorNombre,
        "ejercicio": p0.ejercicio.anio if p0.ejercicio else 0,
        "fechaCreacion": p0.creado_en.isoformat() if p0.creado_en else "",
        "ultimaActualizacion": p0.actualizado_en.isoformat() if p0.actualizado_en else None,
        "presupuestoAsignado": total_presupuesto_asignado,
        "presupuesto": {
            "recursosFiscales": total_fiscales,
            "participaciones": total_participaciones,
            "faismun": total_faismun,
            "fortamun": total_fortamun,
            "otros": total_otros
        },
        "estadoFlujo": p0.estado_flujo or "configuracion"
    }


@router.put("/{clave}/estado", response_model=ProgramaOut)
def actualizar_estado_programa(
    clave: str,
    estado: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Validar rol de planeacion o administrador
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes. Requiere rol planeacion o administrador.")

    programas = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave).all()
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    estados_validos = ["configuracion", "en_captura", "en_revision", "finalizado"]
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Debe ser uno de: {estados_validos}")

    for programa in programas:
        programa.estado_flujo = estado
    db.commit()

    programas = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave).all()
    p0 = programas[0]
    
    # Aggregate executors
    units = []
    seen_units = set()
    for p in programas:
        if p.unidad_administrativa and p.unidad_administrativa.id not in seen_units:
            units.append(p.unidad_administrativa)
            seen_units.add(p.unidad_administrativa.id)
            
    ejecutorClave = ", ".join([u.clave for u in units])
    ejecutorNombre = ", ".join([u.nombre for u in units])
    
    # Aggregate budgets
    total_presupuesto_asignado = 0.0
    total_fiscales = 0.0
    total_participaciones = 0.0
    total_faismun = 0.0
    total_fortamun = 0.0
    total_otros = 0.0
    
    for p in programas:
        pres = obtener_presupuesto_programa(db, p.unidad_administrativa_id, p.ejercicio_id)
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
        "ejecutorClave": ejecutorClave,
        "ejecutorNombre": ejecutorNombre,
        "ejercicio": p0.ejercicio.anio if p0.ejercicio else 0,
        "fechaCreacion": p0.creado_en.isoformat() if p0.creado_en else "",
        "ultimaActualizacion": p0.actualizado_en.isoformat() if p0.actualizado_en else None,
        "presupuestoAsignado": total_presupuesto_asignado,
        "presupuesto": {
            "recursosFiscales": total_fiscales,
            "participaciones": total_participaciones,
            "faismun": total_faismun,
            "fortamun": total_fortamun,
            "otros": total_otros
        },
        "estadoFlujo": p0.estado_flujo or "configuracion"
    }


@router.get("/actividades/{actividad_id}", response_model=ActividadOut)
def obtener_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    actividad = db.query(Actividades).filter(Actividades.id == actividad_id).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    # Si es ejecutor, verificar que pertenezca a su unidad administrativa
    if current_user.rol == RolUsuario.EJECUTOR:
        unidad_id = actividad.componente.programa.unidad_administrativa_id
        if unidad_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    meses_nombres = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    linea_accion_pmd = ", ".join([pmd.clave for pmd in actividad.lineas_pmd]) if actividad.lineas_pmd else "N/A"

    metas_dict = {m.mes: m for m in actividad.metas_mensuales}
    programacion_mensual = []
    for num_mes in range(1, 13):
        nombre_mes = meses_nombres[num_mes]
        meta_record = metas_dict.get(num_mes)
        
        estado = "en_revision"
        avance_meta = 0
        status_val = "BORRADOR"
        comentarios_val = None
        evidencias_val = []
        
        if meta_record:
            avance = meta_record.avance
            if avance:
                avance_meta = avance.avance_meta
                status_val = avance.status.value if avance.status else "BORRADOR"
                comentarios_val = avance.comentarios_revision
                evidencias_val = [
                    {
                        "id": ev.id,
                        "nombre_original": ev.nombre_original,
                        "url_archivo": ev.url_archivo,
                        "mime_type": ev.mime_type
                    }
                    for ev in avance.evidencias if ev.activo
                ]
                if avance.status == StatusAvance.FINALIZADO:
                    estado = "finalizado"

        programacion_mensual.append({
            "mes": nombre_mes,
            "mesNumero": num_mes,
            "meta": meta_record.cantidad_programada if meta_record else 0,
            "estado": estado,
            "avanceMeta": avance_meta,
            "status": status_val,
            "evidencias": evidencias_val,
            "comentarios": comentarios_val
        })

    unidad_clave = actividad.componente.programa.unidad_administrativa.clave if (
        actividad.componente and actividad.componente.programa and actividad.componente.programa.unidad_administrativa
    ) else ""

    return {
        "id": actividad.id,
        "programaClave": actividad.componente.programa.clave if actividad.componente and actividad.componente.programa else "",
        "componenteClave": actividad.componente.clave if actividad.componente else "",
        "clave": actividad.clave,
        "descripcion": actividad.descripcion,
        "metaAnual": actividad.meta,
        "costoEstimado": float(actividad.monto or 0),
        "unidadAdministrativaClave": unidad_clave,
        "lineaAccionPmd": linea_accion_pmd,
        "programacionMensual": programacion_mensual
    }


@router.get("/{clave}/componentes", response_model=list[ComponenteOut])
def listar_componentes(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave)
    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )
    programas = query.all()
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    prog_ids = [p.id for p in programas]

    componentes = (
        db.query(Componentes)
        .filter(Componentes.programa_id.in_(prog_ids))
        .order_by(Componentes.clave)
        .all()
    )
    return [
        {
            "id": c.id,
            "programaClave": clave,
            "clave": c.clave,
            "descripcion": c.descripcion,
        }
        for c in componentes
    ]


@router.get("/{clave}/actividades", response_model=list[ActividadOut])
def listar_actividades(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave)
    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )
    programas = query.all()
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    prog_ids = [p.id for p in programas]

    actividades = (
        db.query(Actividades)
        .join(Componentes, Actividades.componente_id == Componentes.id)
        .filter(Componentes.programa_id.in_(prog_ids))
        .order_by(Actividades.clave)
        .all()
    )

    meses_nombres = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }

    res = []
    for a in actividades:
        linea_accion_pmd = ", ".join([pmd.clave for pmd in a.lineas_pmd]) if a.lineas_pmd else "N/A"

        # Cargar programación mensual
        metas_dict = {m.mes: m for m in a.metas_mensuales}
        programacion_mensual = []
        for num_mes in range(1, 13):
            nombre_mes = meses_nombres[num_mes]
            meta_record = metas_dict.get(num_mes)
            
            estado = "en_revision"
            avance_meta = 0
            status_val = "BORRADOR"
            comentarios_val = None
            evidencias_val = []
            
            if meta_record:
                avance = meta_record.avance
                if avance:
                    avance_meta = avance.avance_meta
                    status_val = avance.status.value if avance.status else "BORRADOR"
                    comentarios_val = avance.comentarios_revision
                    evidencias_val = [
                        {
                            "id": ev.id,
                            "nombre_original": ev.nombre_original,
                            "url_archivo": ev.url_archivo,
                            "mime_type": ev.mime_type
                        }
                        for ev in avance.evidencias if ev.activo
                    ]
                    if avance.status == StatusAvance.FINALIZADO:
                        estado = "finalizado"

            programacion_mensual.append({
                "mes": nombre_mes,
                "mesNumero": num_mes,
                "meta": meta_record.cantidad_programada if meta_record else 0,
                "estado": estado,
                "avanceMeta": avance_meta,
                "status": status_val,
                "evidencias": evidencias_val,
                "comentarios": comentarios_val
            })

        unidad_clave = a.componente.programa.unidad_administrativa.clave if (
            a.componente and a.componente.programa and a.componente.programa.unidad_administrativa
        ) else ""

        res.append({
            "id": a.id,
            "programaClave": clave,
            "componenteClave": a.componente.clave if a.componente else "",
            "clave": a.clave,
            "descripcion": a.descripcion,
            "metaAnual": a.meta,
            "costoEstimado": float(a.monto or 0),
            "unidadAdministrativaClave": unidad_clave,
            "lineaAccionPmd": linea_accion_pmd,
            "programacionMensual": programacion_mensual
        })
    return res


class RevisionInput(BaseModel):
    accion: str
    comentario: Optional[str] = None


@router.post("/actividades/{actividad_id}/mes/{mes}/avance")
def guardar_avance_mensual(
    actividad_id: int,
    mes: int,
    avance_meta: int = Form(...),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Find meta record
    meta = db.query(ProgramacionMeta).filter(
        ProgramacionMeta.actividad_id == actividad_id,
        ProgramacionMeta.mes == mes
    ).first()
    if not meta:
        raise HTTPException(status_code=404, detail="Programación mensual no encontrada")

    # Check if period is active (within date range)
    periodo = db.query(CapturaPeriodos).filter(CapturaPeriodos.mes == mes).first()
    if not periodo:
        raise HTTPException(status_code=400, detail="Periodo de captura no configurado")

    now = datetime.datetime.now()
    if not (periodo.fecha_inicio_reporte <= now <= periodo.fecha_fin_reporte):
        raise HTTPException(
            status_code=400,
            detail=f"El periodo de captura para este mes no está activo ({periodo.fecha_inicio_reporte.strftime('%d/%m/%Y')} - {periodo.fecha_fin_reporte.strftime('%d/%m/%Y')})"
        )

    # Find or create the progress record
    avance = db.query(ProgramacionAvance).filter(
        ProgramacionAvance.programacion_meta_id == meta.id
    ).first()

    if not avance:
        avance = ProgramacionAvance(
            programacion_meta_id=meta.id,
            avance_meta=avance_meta,
            status=StatusAvance.ENVIADO,
            fecha_envio=now
        )
        db.add(avance)
        db.flush()
    else:
        if avance.status == StatusAvance.FINALIZADO:
            raise HTTPException(status_code=400, detail="El avance de este mes ya ha sido finalizado y aprobado")
        avance.avance_meta = avance_meta
        avance.status = StatusAvance.ENVIADO
        avance.fecha_envio = now

    # Save all uploaded files
    for file in files:
        if file and file.filename:
            os.makedirs("uploads", exist_ok=True)
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join("uploads", unique_filename)

            with open(file_path, "wb") as f:
                f.write(file.file.read())

            evidencia = ProgramacionEvidencia(
                programacion_avance_id=avance.id,
                nombre_original=file.filename,
                url_archivo=file_path,
                mime_type=file.content_type or "application/octet-stream"
            )
            db.add(evidencia)

    db.commit()
    return {"status": "success", "message": "Avance mensual guardado y enviado a revisión"}


@router.get("/evidencia/download/{evidencia_id}")
def descargar_evidencia(
    evidencia_id: int,
    db: Session = Depends(get_db)
):
    ev = db.query(ProgramacionEvidencia).filter(ProgramacionEvidencia.id == evidencia_id).first()
    if not ev or not ev.activo:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    if not os.path.exists(ev.url_archivo):
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado en el servidor")

    return FileResponse(ev.url_archivo, filename=ev.nombre_original, media_type=ev.mime_type)


@router.put("/actividades/{actividad_id}/mes/{mes}/revision")
def revisar_avance_mensual(
    actividad_id: int,
    mes: int,
    data: RevisionInput,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    # Check permissions
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar revisiones")

    meta = db.query(ProgramacionMeta).filter(
        ProgramacionMeta.actividad_id == actividad_id,
        ProgramacionMeta.mes == mes
    ).first()
    if not meta:
        raise HTTPException(status_code=404, detail="Programación mensual no encontrada")

    avance = db.query(ProgramacionAvance).filter(
        ProgramacionAvance.programacion_meta_id == meta.id
    ).first()

    if not avance:
        raise HTTPException(status_code=404, detail="Avance no encontrado para este periodo")

    if data.accion == "aprobar":
        avance.status = StatusAvance.FINALIZADO
        avance.comentarios_revision = None
    elif data.accion == "devolver":
        avance.status = StatusAvance.CORRECCION
        avance.comentarios_revision = data.comentario
    else:
        raise HTTPException(status_code=400, detail="Acción inválida. Use 'aprobar' o 'devolver'.")

    avance.fecha_revision = datetime.datetime.now()
    db.commit()
    return {"status": "success", "message": f"Avance mensual revisado con éxito ({data.accion})"}
