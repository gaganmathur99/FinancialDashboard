from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.db.base import engine, Base, get_db
from backend.app.db.init_db import init_db
from backend.app.api.api import api_router
from backend.app.core.config import settings

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="0.1.0",
)

# Configure CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on startup.
    """
    db = next(get_db())
    init_db(db)


@app.get("/")
def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {
        "message": "Welcome to the Personal Finance API",
        "version": "0.1.0",
        "docs_url": "/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify the API is running and connected to the database.
    """
    try:
        # Check if the database is reachable
        result = db.execute("SELECT 1").first()
        return {
            "status": "ok",
            "database": "connected" if result else "disconnected",
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
    "backend.app.main:app",
    host="0.0.0.0" if settings.SERVER_HOST == "localhost" else settings.SERVER_HOST,
    port=settings.SERVER_PORT,
    reload=settings.DEBUG,
)