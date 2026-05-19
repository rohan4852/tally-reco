from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app.routes import health, upload, parse, reconcile
# NOTE: routers are under backend/app/routes/ as a package-less directory.
# Import path `app.routes` assumes Python can find `app/routes` as a namespace.
# If this fails, run `uvicorn backend.app.main:app` from the backend/ dir.


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(parse.router)
app.include_router(reconcile.router)

@app.get("/", tags=["Root"])
async def root() -> dict:
    return {
        "message": "GST Reconciliation API is running.",
        "docs": "/docs",
        "health": "/health",
    }