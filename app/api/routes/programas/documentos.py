from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, require_entidad_match, get_db
from app.crud.programas import actividades as actividades_crud
from app.models.usuario import RolUsuario
from app.schemas.programas.inputs import FormatoEvidenciaInput
from app.services.programas.formato_evidencia import generate_formato_evidencia_document

router = APIRouter()

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


@router.post("/actividades/{actividad_id}/mes/{mes}/formato-evidencia")
def generar_formato_evidencia(
    actividad_id: int,
    mes: int,
    body: FormatoEvidenciaInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    actividad = actividades_crud.get_actividad_by_id(
        db, actividad_id, entidad_id=current_user.entidad_id
    )
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    if current_user.rol == RolUsuario.EJECUTOR:
        unidad_id = actividad.componente.programa.unidad_administrativa_id
        if unidad_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    try:
        document, filename = generate_formato_evidencia_document(
            db,
            actividad_id,
            mes,
            justificacion_tecnica=body.justificacion_tecnica,
            evidencias_input=body.evidencias,
            base_url=str(request.base_url).rstrip("/"),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return StreamingResponse(
        document,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
