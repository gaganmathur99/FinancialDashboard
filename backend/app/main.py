from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.api.endpoints import auth, accounts
from backend.app.core.config import API_V1_PREFIX, PROJECT_NAME, ALLOWED_ORIGINS, DEBUG
from backend.app.db.init_db import init_db

app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_V1_PREFIX}/openapi.json",
    docs_url=f"{API_V1_PREFIX}/docs",
    redoc_url=f"{API_V1_PREFIX}/redoc",
    debug=DEBUG
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth.router,
    prefix=f"{API_V1_PREFIX}/auth",
    tags=["authentication"]
)

app.include_router(
    accounts.router,
    prefix=f"{API_V1_PREFIX}/accounts",
    tags=["accounts"]
)

@app.get("/", tags=["root"])
def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to the Personal Finance API",
        "docs": f"{API_V1_PREFIX}/docs"
    }

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.on_event("startup")
def startup_db_client():
    """
    Initialize the database on startup
    """
    db = next(get_db())
    init_db(db)