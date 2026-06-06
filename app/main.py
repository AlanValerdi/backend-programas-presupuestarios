from fastapi import FastAPI
from app.api.routes.etl import router as etl_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.programas import router as programas_router
from app.api.routes.fechas_captura import router as fechas_captura_router
from app.api.routes.usuarios import router as usuarios_router

app = FastAPI()

app.include_router(etl_router)
app.include_router(unidades_router)
app.include_router(programas_router)
app.include_router(fechas_captura_router)
app.include_router(usuarios_router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

