from sqlalchemy.orm import Session
from app.models.usuario import Usuario, RolUsuario
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.core.security import hashear_password, verificar_password


def get_usuario_by_username(
    db: Session, username: str, entidad_id: int | None = None
) -> Usuario | None:
    query = db.query(Usuario).filter(Usuario.username == username)
    if entidad_id is not None:
        query = query.filter(Usuario.entidad_id == entidad_id)
    return query.first()


def get_usuario_by_email(
    db: Session, email: str, entidad_id: int | None = None
) -> Usuario | None:
    query = db.query(Usuario).filter(Usuario.email == email)
    if entidad_id is not None:
        query = query.filter(Usuario.entidad_id == entidad_id)
    return query.first()


def get_usuario_by_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuarios(
    db: Session, entidad_id: int, skip: int = 0, limit: int = 100
) -> list[Usuario]:
    return (
        db.query(Usuario)
        .filter(Usuario.activo == True, Usuario.entidad_id == entidad_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_usuario(db: Session, usuario_in: UsuarioCreate, entidad_id: int) -> Usuario:
    hashed = hashear_password(usuario_in.password)
    
    active_unit_id = usuario_in.unidad_administrativa_id
    if active_unit_id is None and usuario_in.unidades_administrativas_ids:
        active_unit_id = usuario_in.unidades_administrativas_ids[0]

    db_usuario = Usuario(
        username=usuario_in.username,
        email=usuario_in.email,
        hashed_password=hashed,
        telefono=usuario_in.telefono,
        rol=usuario_in.rol,
        entidad_id=entidad_id,
        unidad_administrativa_id=active_unit_id,
    )

    if usuario_in.unidades_administrativas_ids:
        unidades = db.query(CatalogoUnidadesAdministrativas).filter(
            CatalogoUnidadesAdministrativas.id.in_(usuario_in.unidades_administrativas_ids),
            CatalogoUnidadesAdministrativas.entidad_id == entidad_id,
        ).all()
        db_usuario.unidades_administrativas = unidades

    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def update_usuario(
    db: Session,
    db_usuario: Usuario,
    usuario_in: UsuarioUpdate,
) -> Usuario:
    update_data = usuario_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = hashear_password(update_data.pop("password"))

    if "unidades_administrativas_ids" in update_data:
        u_ids = update_data.pop("unidades_administrativas_ids")
        if u_ids is not None:
            unidades = db.query(CatalogoUnidadesAdministrativas).filter(
                CatalogoUnidadesAdministrativas.id.in_(u_ids),
                CatalogoUnidadesAdministrativas.entidad_id == db_usuario.entidad_id,
            ).all()
            db_usuario.unidades_administrativas = unidades
            if db_usuario.unidad_administrativa_id not in u_ids:
                db_usuario.unidad_administrativa_id = u_ids[0] if u_ids else None
        else:
            db_usuario.unidades_administrativas = []
            db_usuario.unidad_administrativa_id = None

    for field, value in update_data.items():
        setattr(db_usuario, field, value)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def authenticate_usuario(
    db: Session,
    username: str,
    password: str,
    entidad_id: int,
) -> Usuario | None:
    db_usuario = get_usuario_by_username(db, username, entidad_id)
    if not db_usuario:
        return None
    if not verificar_password(password, db_usuario.hashed_password):
        return None
    return db_usuario


def get_usuarios_by_unidad(
    db: Session,
    unidad_administrativa_id: int,
    entidad_id: int,
) -> list[Usuario]:
    return (
        db.query(Usuario)
        .filter(
            Usuario.unidad_administrativa_id == unidad_administrativa_id,
            Usuario.entidad_id == entidad_id,
            Usuario.activo == True,
        )
        .all()
    )
