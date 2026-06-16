from sqlalchemy.orm import Session

from app.api.dependencies import TokenData
from app.models.catalogo_programas import CatalogoProgramas
from app.models.usuario import RolUsuario


def get_programas_query(db: Session, current_user: TokenData):
    query = db.query(CatalogoProgramas)
    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )
    return query


def list_programas(db: Session, current_user: TokenData) -> list[CatalogoProgramas]:
    return get_programas_query(db, current_user).order_by(CatalogoProgramas.clave).all()


def get_programas_by_clave(
    db: Session,
    clave: str,
    current_user: TokenData,
) -> list[CatalogoProgramas]:
    query = get_programas_query(db, current_user).filter(CatalogoProgramas.clave == clave)
    return query.all()


def update_estado_programa(db: Session, clave: str, estado: str) -> None:
    programas = db.query(CatalogoProgramas).filter(CatalogoProgramas.clave == clave).all()
    for programa in programas:
        programa.estado_flujo = estado
    db.commit()
