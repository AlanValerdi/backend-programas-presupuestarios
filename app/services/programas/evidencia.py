import os
import uuid

from fastapi import UploadFile

from app.models.programacion_evidencia import ProgramacionEvidencia


def save_evidencia_file(file: UploadFile, avance_id: int) -> ProgramacionEvidencia:
    os.makedirs("uploads", exist_ok=True)
    file_ext = os.path.splitext(file.filename or "")[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join("uploads", unique_filename)

    with open(file_path, "wb") as output:
        output.write(file.file.read())

    return ProgramacionEvidencia(
        programacion_avance_id=avance_id,
        nombre_original=file.filename or unique_filename,
        url_archivo=file_path,
        mime_type=file.content_type or "application/octet-stream",
    )


def remove_evidencia_file(url_archivo: str | None) -> None:
    if url_archivo and os.path.exists(url_archivo):
        os.remove(url_archivo)
