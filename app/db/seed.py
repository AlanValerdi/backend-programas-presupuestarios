from calendar import monthrange
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD
from app.core.security import hashear_password
from app.db.database import SessionLocal
from app.models.captura_periodos import CapturaPeriodos
from app.models.catalogo_programas import CatalogoProgramas
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.models.ejercicio import Ejercicio
from app.models.entidad import Entidad
from app.models.entity_field_contract import EntityFieldContract, EntityType
from app.models.usuario import Usuario, RolUsuario

DEFAULT_EJERCICIO_ANIO = 2026


def get_or_create_entidad(db: Session, slug: str, nombre: str) -> Entidad:
    entidad = db.query(Entidad).filter(Entidad.slug == slug).first()
    if entidad:
        return entidad
    entidad = Entidad(slug=slug, nombre=nombre, activo=True)
    db.add(entidad)
    db.commit()
    db.refresh(entidad)
    return entidad


def ensure_contract(
    db: Session,
    entidad: Entidad,
    entity_type: str,
    fields: list[dict],
) -> EntityFieldContract:
    contract = (
        db.query(EntityFieldContract)
        .filter(
            EntityFieldContract.entidad_id == entidad.id,
            EntityFieldContract.entity_type == entity_type,
        )
        .first()
    )
    if contract:
        contract.fields = fields
        db.commit()
        db.refresh(contract)
        return contract
    contract = EntityFieldContract(
        entidad_id=entidad.id,
        entity_type=entity_type,
        fields=fields,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def seed_ejercicio(
    db: Session, entidad: Entidad, anio: int = DEFAULT_EJERCICIO_ANIO
) -> Ejercicio:
    ejercicio = (
        db.query(Ejercicio)
        .filter(Ejercicio.anio == anio, Ejercicio.entidad_id == entidad.id)
        .first()
    )
    if ejercicio:
        if not ejercicio.activo:
            db.query(Ejercicio).filter(
                Ejercicio.entidad_id == entidad.id, Ejercicio.id != ejercicio.id
            ).update({"activo": False})
            ejercicio.activo = True
            db.commit()
            db.refresh(ejercicio)
        return ejercicio

    db.query(Ejercicio).filter(Ejercicio.entidad_id == entidad.id).update(
        {"activo": False}
    )

    ejercicio = Ejercicio(
        anio=anio,
        entidad_id=entidad.id,
        fecha_inicio_planeacion=datetime(anio, 1, 1, 0, 0, 0),
        fecha_fin_planeacion=datetime(anio, 12, 31, 23, 59, 59),
        planeacion_abierta=False,
        mostrar_montos=True,
        activo=True,
    )
    db.add(ejercicio)
    db.commit()
    db.refresh(ejercicio)
    return ejercicio


def seed_captura_periodos(db: Session, ejercicio: Ejercicio) -> int:
    existing = (
        db.query(CapturaPeriodos)
        .filter(CapturaPeriodos.ejercicio_id == ejercicio.id)
        .count()
    )
    if existing > 0:
        return 0

    created = 0
    for mes in range(1, 13):
        _, last_day = monthrange(ejercicio.anio, mes)
        periodo = CapturaPeriodos(
            mes=mes,
            fecha_inicio_reporte=datetime(ejercicio.anio, mes, 1, 0, 0, 0),
            fecha_fin_reporte=datetime(ejercicio.anio, mes, last_day, 23, 59, 59),
            ejercicio_id=ejercicio.id,
            activo=True,
        )
        db.add(periodo)
        created += 1

    db.commit()
    return created


def ensure_admin(db: Session, entidad: Entidad, username: str, email: str, password: str) -> Usuario:
    user = (
        db.query(Usuario)
        .filter(Usuario.username == username, Usuario.entidad_id == entidad.id)
        .first()
    )
    if user:
        return user
    user = Usuario(
        username=username,
        email=email,
        hashed_password=hashear_password(password),
        rol=RolUsuario.ADMINISTRADOR,
        activo=True,
        entidad_id=entidad.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_atlixco_demo(db: Session, entidad: Entidad, ejercicio: Ejercicio) -> None:
    unidad = (
        db.query(CatalogoUnidadesAdministrativas)
        .filter(
            CatalogoUnidadesAdministrativas.entidad_id == entidad.id,
            CatalogoUnidadesAdministrativas.clave == "01",
        )
        .first()
    )
    if not unidad:
        unidad = CatalogoUnidadesAdministrativas(
            clave="01",
            nombre="Presidencia Municipal Atlixco",
            plazas=10,
            activo=True,
            entidad_id=entidad.id,
        )
        db.add(unidad)
        db.commit()
        db.refresh(unidad)

    programa = (
        db.query(CatalogoProgramas)
        .filter(
            CatalogoProgramas.entidad_id == entidad.id,
            CatalogoProgramas.clave == "ATL-001",
            CatalogoProgramas.ejercicio_id == ejercicio.id,
        )
        .first()
    )
    if not programa:
        programa = CatalogoProgramas(
            clave="ATL-001",
            programa="Programa demostrativo Atlixco",
            entidad_id=entidad.id,
            ejercicio_id=ejercicio.id,
            unidad_administrativa_id=unidad.id,
            activo=True,
            estado_flujo="en_captura",
            campos_extra={
                "datosExtraPrograma": "Datos de ejemplo para el municipio de Atlixco"
            },
        )
        db.add(programa)
        db.commit()
    elif not programa.campos_extra:
        programa.campos_extra = {
            "datosExtraPrograma": "Datos de ejemplo para el municipio de Atlixco"
        }
        db.commit()


def run_seed(anio: int = DEFAULT_EJERCICIO_ANIO) -> None:
    db = SessionLocal()
    try:
        huachinango = get_or_create_entidad(db, "huachinango", "Huachinango")
        atlixco = get_or_create_entidad(db, "atlixco", "Atlixco")

        ensure_contract(db, huachinango, EntityType.PROGRAMA, [])
        ensure_contract(db, huachinango, EntityType.ACTIVIDAD, [])
        ensure_contract(
            db,
            atlixco,
            EntityType.PROGRAMA,
            [
                {
                    "key": "datosExtraPrograma",
                    "label": "Datos extra del programa presupuestal",
                    "type": "string",
                    "required": False,
                }
            ],
        )
        ensure_contract(db, atlixco, EntityType.ACTIVIDAD, [])

        ej_hua = seed_ejercicio(db, huachinango, anio=anio)
        periodos_hua = seed_captura_periodos(db, ej_hua)
        ensure_admin(db, huachinango, ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)

        ej_atl = seed_ejercicio(db, atlixco, anio=anio)
        periodos_atl = seed_captura_periodos(db, ej_atl)
        ensure_admin(
            db,
            atlixco,
            ADMIN_USERNAME,
            f"admin@{atlixco.slug}.gob.mx",
            ADMIN_PASSWORD,
        )
        seed_atlixco_demo(db, atlixco, ej_atl)

        print(
            f"Seed OK: huachinango ejercicio {ej_hua.anio} "
            f"(periodos={periodos_hua}); atlixco ejercicio {ej_atl.anio} "
            f"(periodos={periodos_atl})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
