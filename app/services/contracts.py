from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entity_field_contract import EntityFieldContract


def get_contract_fields(db: Session, entidad_id: int, entity_type: str) -> list[dict]:
    contract = (
        db.query(EntityFieldContract)
        .filter(
            EntityFieldContract.entidad_id == entidad_id,
            EntityFieldContract.entity_type == entity_type,
        )
        .first()
    )
    return list(contract.fields) if contract and contract.fields else []


def validate_campos_extra(
    db: Session,
    entidad_id: int,
    entity_type: str,
    campos_extra: dict[str, Any] | None,
) -> dict[str, Any]:
    extras = campos_extra or {}
    if not isinstance(extras, dict):
        raise HTTPException(status_code=400, detail="campos_extra must be an object")

    allowed = get_contract_fields(db, entidad_id, entity_type)
    allowed_map = {f["key"]: f for f in allowed if isinstance(f, dict) and "key" in f}

    unknown = [k for k in extras.keys() if k not in allowed_map]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown campos_extra keys for {entity_type}: {unknown}",
        )

    for key, spec in allowed_map.items():
        if spec.get("required") and (key not in extras or extras[key] in (None, "")):
            raise HTTPException(
                status_code=400,
                detail=f"Required campo_extra '{key}' is missing",
            )
        if key in extras and extras[key] is not None:
            expected = spec.get("type", "string")
            value = extras[key]
            if expected == "string" and not isinstance(value, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"campo_extra '{key}' must be a string",
                )
            if expected == "number" and not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=400,
                    detail=f"campo_extra '{key}' must be a number",
                )
            if expected == "boolean" and not isinstance(value, bool):
                raise HTTPException(
                    status_code=400,
                    detail=f"campo_extra '{key}' must be a boolean",
                )

    return extras
