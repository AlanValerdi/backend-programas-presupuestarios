from sqlalchemy.orm import Session

from app.models.programacion_evidencia import ProgramacionEvidencia


def get_evidencia_by_id(db: Session, evidencia_id: int) -> ProgramacionEvidencia | None:
    return (
        db.query(ProgramacionEvidencia)
        .filter(ProgramacionEvidencia.id == evidencia_id)
        .first()
    )
