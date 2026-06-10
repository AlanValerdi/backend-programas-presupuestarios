from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.models.usuario import RolUsuario


class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    rol: str = Field(default=RolUsuario.EJECUTOR)
    unidad_administrativa_id: Optional[int] = None
    mostrar_montos: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)
    unidades_administrativas_ids: Optional[list[int]] = None

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        roles_validos = [
            RolUsuario.ADMINISTRADOR,
            RolUsuario.PROGRAMACION_PRESUPUESTAL,
            RolUsuario.PLANEACION,
            RolUsuario.EJECUTOR,
        ]
        if v not in roles_validos:
            raise ValueError(
                f"Rol inválido. Debe ser uno de: {roles_validos}"
            )
        return v

    @field_validator("rol")
    @classmethod
    def bloquear_creacion_admin(cls, v: str) -> str:
        if v == RolUsuario.ADMINISTRADOR:
            raise ValueError(
                "No se puede crear un usuario con rol 'administrador' vía API. "
                "Este rol debe crearse manualmente en la base de datos."
            )
        return v

    @field_validator("unidad_administrativa_id")
    @classmethod
    def validar_unidad_ejecutor(cls, v: Optional[int], info) -> Optional[int]:
        data = info.data
        if data.get("rol") == RolUsuario.EJECUTOR and v is None:
            raise ValueError(
                "Los usuarios con rol 'ejecutores' deben tener unidad_administrativa_id"
            )
        return v


class UsuarioUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    rol: Optional[str] = None
    unidad_administrativa_id: Optional[int] = None
    unidades_administrativas_ids: Optional[list[int]] = None
    activo: Optional[bool] = None
    mostrar_montos: Optional[bool] = None

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        roles_validos = [
            RolUsuario.ADMINISTRADOR,
            RolUsuario.PROGRAMACION_PRESUPUESTAL,
            RolUsuario.PLANEACION,
            RolUsuario.EJECUTOR,
        ]
        if v not in roles_validos:
            raise ValueError(
                f"Rol inválido. Debe ser uno de: {roles_validos}"
            )
        return v

    @field_validator("rol")
    @classmethod
    def bloquear_cambio_a_admin(cls, v: Optional[str]) -> Optional[str]:
        if v == RolUsuario.ADMINISTRADOR:
            raise ValueError(
                "No se puede asignar el rol 'administrador' vía API. "
                "Este rol debe asignarse manualmente en la base de datos."
            )
        return v


class UnidadSimpleOut(BaseModel):
    id: int
    clave: str
    nombre: str

    class Config:
        from_attributes = True


class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    unidades_administrativas: list[UnidadSimpleOut] = []

    class Config:
        from_attributes = True


class UsuarioConPassword(UsuarioOut):
    hashed_password: str