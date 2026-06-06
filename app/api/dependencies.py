from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.core.config import SECRET_KEY, ALGORITHM
from app.models.usuario import RolUsuario


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TokenData:
    def __init__(self, sub: str, rol: str, unidad_administrativa_id: int | None):
        self.sub = sub
        self.rol = rol
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
        unidad_administrativa_id: Optional[int] = payload.get("unidad_administrativa_id")
        if sub is None:
            raise credentials_exception
        return TokenData(sub=sub, rol=rol, unidad_administrativa_id=unidad_administrativa_id)
    except jwt.PyJWTError:
        raise credentials_exception


def require_roles(*roles: str):
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles}",
            )
        return current_user
    return role_checker


def require_planeacion():
    return require_roles(RolUsuario.PLANEACION, RolUsuario.PROGRAMACION_PRESUPUESTAL)


def require_programacion_presupuestal():
    return require_roles(RolUsuario.PROGRAMACION_PRESUPUESTAL)


def require_ejecutor():
    return require_roles(RolUsuario.EJECUTOR)


def require_any_role():
    return require_roles(
        RolUsuario.PROGRAMACION_PRESUPUESTAL,
        RolUsuario.PLANEACION,
        RolUsuario.EJECUTOR,
    )