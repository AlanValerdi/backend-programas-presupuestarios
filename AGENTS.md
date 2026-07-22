# AGENTS.md

- Do not commit or push unless the user explicitly asks.
- FastAPI entrypoint is `app/main.py` (Uvicorn app = `app`).
- SQLAlchemy setup lives in `app/db/database.py`; it loads `.env` via `python-dotenv` and expects `SQLALCHEMY_DATABASE_URL`.
- Alembic autogenerate relies on models being imported in `app/models/__init__.py` to populate `Base.metadata`.
- Alembic config is in `alembic.ini` (default `sqlalchemy.url` is local Postgres `gpp-db`).
- Project structure conventions: `app/core` for settings/security, `app/api` for routers/dependencies, `app/models` for DB models, `app/schemas` for Pydantic schemas, `app/crud` for DB access, `app/services` for external/business logic, `app/db` for engine/session/migrations, `tests` for pytest.
