from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user, TokenData
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.actividades import Actividades
from app.models.usuario import RolUsuario
from app.schemas.programas import ProgramaOut, ComponenteOut, ActividadOut


router = APIRouter(prefix="/api/programas", tags=["programas"])


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
    return [
        {
            "id": p.id,
            "clave": p.clave,
            "descripcion": p.programa,
            "ejecutorClave": p.unidad_administrativa.clave
            if p.unidad_administrativa
            else "",
            "ejecutorNombre": p.unidad_administrativa.nombre
            if p.unidad_administrativa
            else "",
            "ejercicio": p.ejercicio.anio if p.ejercicio else 0,
            "fechaCreacion": p.creado_en.isoformat() if p.creado_en else "",
            "ultimaActualizacion": p.actualizado_en.isoformat()
            if p.actualizado_en
            else None,
        }
        for p in programas
    ]


@router.get("/{clave}", response_model=ProgramaOut)
def obtener_programa(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programa = (
        db.query(CatalogoProgramas)
        .filter(CatalogoProgramas.clave == clave)
        .first()
    )
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    if current_user.rol == RolUsuario.EJECUTOR:
        if programa.unidad_administrativa_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": programa.id,
        "clave": programa.clave,
        "descripcion": programa.programa,
        "ejecutorClave": programa.unidad_administrativa.clave
        if programa.unidad_administrativa
        else "",
        "ejecutorNombre": programa.unidad_administrativa.nombre
        if programa.unidad_administrativa
        else "",
        "ejercicio": programa.ejercicio.anio if programa.ejercicio else 0,
        "fechaCreacion": programa.creado_en.isoformat() if programa.creado_en else "",
        "ultimaActualizacion": programa.actualizado_en.isoformat()
        if programa.actualizado_en
        else None,
    }


@router.get("/{clave}/componentes", response_model=list[ComponenteOut])
def listar_componentes(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programa = (
        db.query(CatalogoProgramas)
        .filter(CatalogoProgramas.clave == clave)
        .first()
    )
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    if current_user.rol == RolUsuario.EJECUTOR:
        if programa.unidad_administrativa_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Access denied")

    componentes = (
        db.query(Componentes)
        .filter(Componentes.programa_id == programa.id)
        .order_by(Componentes.clave)
        .all()
    )
    return [
        {
            "id": c.id,
            "programaClave": programa.clave,
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
    programa = (
        db.query(CatalogoProgramas)
        .filter(CatalogoProgramas.clave == clave)
        .first()
    )
    if not programa:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    if current_user.rol == RolUsuario.EJECUTOR:
        if programa.unidad_administrativa_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Access denied")

    actividades = (
        db.query(Actividades)
        .join(Componentes, Actividades.componente_id == Componentes.id)
        .filter(Componentes.programa_id == programa.id)
        .order_by(Actividades.clave)
        .all()
    )
    return [
        {
            "id": a.id,
            "programaClave": programa.clave,
            "componenteClave": a.componente.clave if a.componente else "",
            "clave": a.clave,
            "descripcion": a.descripcion,
            "metaAnual": a.meta,
            "costoEstimado": float(a.monto or 0),
            "unidadAdministrativaClave": programa.unidad_administrativa.clave
            if programa.unidad_administrativa
            else "",
        }
        for a in actividades
    ]
