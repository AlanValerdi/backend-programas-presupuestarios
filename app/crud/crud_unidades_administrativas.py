from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.inter_techo_financiero import TechoFinanciero
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas 

def obtener_presupuesto_unidades(db: Session, ejercicio_id: int):
    # Esto genera un equivalente a: SELECT unidad, SUM(monto) FROM techos GROUP BY unidad
    resultados = db.query(
        CatalogoUnidadesAdministrativas.nombre,
        func.sum(TechoFinanciero.monto).label('total_proyectado')
    ).join(
        TechoFinanciero, 
        CatalogoUnidadesAdministrativas.id == TechoFinanciero.unidad_administrativa_id
    ).filter(
        TechoFinanciero.ejercicio_id == ejercicio_id
    ).group_by(
        CatalogoUnidadesAdministrativas.nombre
    ).all()
    
    return resultados