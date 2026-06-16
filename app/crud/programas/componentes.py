from sqlalchemy.orm import Session

from app.models.componentes import Componentes


def get_componentes_by_programa_ids(db: Session, programa_ids: list[int]) -> list[Componentes]:
    return (
        db.query(Componentes)
        .filter(Componentes.programa_id.in_(programa_ids))
        .all()
    )
