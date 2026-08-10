from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.dependencies import (
    get_db,
    TokenData,
    require_any_role,
    require_roles,
    get_entidad_from_slug,
    require_entidad_match,
)
from app.crud import crud_usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.core.security import crear_token_acceso
from app.models.usuario import RolUsuario
from app.models.entidad import Entidad


router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def register_usuario(
    usuario_in: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_roles(RolUsuario.PLANEACION)),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    existing = crud_usuario.get_usuario_by_username(db, usuario_in.username, entidad.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    existing_email = crud_usuario.get_usuario_by_email(db, usuario_in.email, entidad.id)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return crud_usuario.create_usuario(db, usuario_in, entidad_id=entidad.id)


@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    user = crud_usuario.authenticate_usuario(
        db, form_data.username, form_data.password, entidad.id
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    token = crear_token_acceso(
        data={"sub": user.username},
        rol=user.rol,
        entidad_id=user.entidad_id,
        unidad_administrativa_id=user.unidad_administrativa_id,
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    current_user: TokenData = Depends(require_entidad_match),
):
    return {"message": "Logout successful", "username": current_user.sub}


@router.get("/me", response_model=UsuarioOut)
def read_current_user(
    current_user: TokenData = Depends(require_entidad_match),
    db: Session = Depends(get_db),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    user = crud_usuario.get_usuario_by_username(db, current_user.sub, entidad.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", response_model=list[UsuarioOut])
def list_usuarios(
    current_user: TokenData = Depends(require_any_role()),
    db: Session = Depends(get_db),
    entidad: Entidad = Depends(get_entidad_from_slug),
    skip: int = 0,
    limit: int = 100,
):
    if current_user.rol == RolUsuario.EJECUTOR:
        usuarios = crud_usuario.get_usuarios_by_unidad(
            db, current_user.unidad_administrativa_id, entidad.id
        )
    else:
        usuarios = crud_usuario.get_usuarios(db, entidad.id, skip=skip, limit=limit)
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(
    usuario_id: int,
    current_user: TokenData = Depends(require_any_role()),
    db: Session = Depends(get_db),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    user = crud_usuario.get_usuario_by_id(db, usuario_id)
    if not user or user.entidad_id != entidad.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.rol == RolUsuario.EJECUTOR:
        if user.unidad_administrativa_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return user


@router.put("/{usuario_id}", response_model=UsuarioOut)
def update_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    current_user: TokenData = Depends(require_any_role()),
    db: Session = Depends(get_db),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    user = crud_usuario.get_usuario_by_id(db, usuario_id)
    if not user or user.entidad_id != entidad.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.rol == RolUsuario.EJECUTOR:
        if user.unidad_administrativa_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if usuario_in.rol and usuario_in.rol != RolUsuario.EJECUTOR:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change role")
    return crud_usuario.update_usuario(db, user, usuario_in)


@router.post("/switch-context/{unidad_id}")
def switch_context(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    from app.models.usuario import Usuario
    user = (
        db.query(Usuario)
        .filter(Usuario.username == current_user.sub, Usuario.entidad_id == entidad.id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    allowed_ids = [u.id for u in user.unidades_administrativas]
    if unidad_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this unit is not authorized for this user",
        )

    user.unidad_administrativa_id = unidad_id
    db.commit()

    token = crear_token_acceso(
        data={"sub": user.username},
        rol=user.rol,
        entidad_id=user.entidad_id,
        unidad_administrativa_id=unidad_id,
    )
    return {"access_token": token, "token_type": "bearer"}
