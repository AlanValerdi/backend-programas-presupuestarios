Backend para programas presupuestales

my_fastapi_project/
├── app/
│   ├── __init__.py
│   ├── main.py               # The Uvicorn entry point
│   ├── core/                 # App-wide settings and configs
│   │   ├── config.py         # Pydantic BaseSettings (env vars)
│   │   └── security.py       # Hashing, JWT tokens
│   ├── api/                  # API Routers (the "Controllers")
│   │   ├── dependencies.py   # Reusable dependencies (e.g., get_db, get_current_user)
│   │   └── routes/
│   │       ├── users.py      # Endpoints: @router.get("/users/")
│   │       └── items.py
│   ├── models/               # Database Models (SQLAlchemy, Tortoise, etc.)
│   │   └── user.py
│   ├── schemas/              # Pydantic Models (Data validation/serialization)
│   │   └── user.py
│   ├── crud/                 # Database interaction logic (Create, Read, Update, Delete)
│   │   └── crud_user.py
│   ├── services/             # External services or complex business logic
│   │   └── email.py
│   └── db/                   # Database connection and session management
│       ├── database.py       # Engine and session maker
│       └── migrations/       # Alembic migrations (if using SQL)
├── tests/                    # Pytest test suite
│   ├── conftest.py
│   └── api/
├── .env                      # Environment variables (do not commit this!)
├── .gitignore
├── requirements.txt          # Or pyproject.toml / Pipfile
└── Dockerfile                # Deployment instructions

--Deuda tecnica
Si quieres que el dry‑run no marque cambios falsos y el JSON se vea limpio: conviene normalizar (Decimal o round a 2 decimales) antes de comparar y responder.

python -c "import secrets; print(secrets.token_hex(32))"