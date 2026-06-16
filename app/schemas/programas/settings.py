from pydantic import BaseModel


class SettingsOut(BaseModel):
    mostrar_montos: bool
