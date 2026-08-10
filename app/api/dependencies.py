from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.core.config import SECRET_KEY, ALGORITHM
from app.models.usuario import RolUsuario
from app.models.entidad import Entidad


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TokenData:
    def __init__(
        self,
        sub: str,
        rol: str,
        entidad_id: int,
        unidad_administrativa_id: int | None,
    ):
        self.sub = sub
        self.rol = rol
        self.entidad_id = entidad_id
        self.unidad_administrativa_id = unidad_administrativa_id


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        rol: str = payload.get("rol")
        entidad_id = payload.get("entidad_id")
        unidad_administrativa_id: Optional[int] = payload.get("unidad_administrativa_id")
        if sub is None or entidad_id is None:
            raise credentials_exception
        return TokenData(
            sub=sub,
            rol=rol,
            entidad_id=int(entidad_id),
            unidad_administrativa_id=unidad_administrativa_id,
        )
    except jwt.PyJWTError:
        raise credentials_exception


def get_entidad_from_slug(
    entidad_slug: str,
    db: Session = Depends(get_db),
) -> Entidad:
    entidad = (
        db.query(Entidad)
        .filter(Entidad.slug == entidad_slug, Entidad.activo == True)
        .first()
    )
    if not entidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entidad '{entidad_slug}' not found",
        )
    return entidad


def require_entidad_match(
    entidad: Entidad = Depends(get_entidad_from_slug),
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    if current_user.entidad_id != entidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token entidad does not match path entidad",
        )
    return current_user


def require_roles(*roles: str):
    def role_checker(current_user: TokenData = Depends(require_entidad_match)):
        if current_user.rol == RolUsuario.ADMINISTRADOR:
            return current_user
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles}",
            )
        return current_user
    return role_checker


def require_admin():
    def admin_checker(current_user: TokenData = Depends(require_entidad_match)):
        if current_user.rol != RolUsuario.ADMINISTRADOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Administrator role required.",
            )
        return current_user
    return admin_checker


def require_planeacion():
    return require_roles(RolUsuario.PLANEACION, RolUsuario.PROGRAMACION_PRESUPUESTAL)


def require_programacion_presupuestal():
    return require_roles(RolUsuario.PROGRAMACION_PRESUPUESTAL)


def require_ejecutor():
    return require_roles(RolUsuario.EJECUTOR)


def require_any_role():
    return require_roles(
        RolUsuario.ADMINISTRADOR,
        RolUsuario.PROGRAMACION_PRESUPUESTAL,
        RolUsuario.PLANEACION,
        RolUsuario.EJECUTOR,
    )
