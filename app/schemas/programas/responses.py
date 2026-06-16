from pydantic import BaseModel


class StatusMessageResponse(BaseModel):
    status: str
    message: str
