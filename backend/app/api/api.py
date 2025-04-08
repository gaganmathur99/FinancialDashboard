from fastapi import APIRouter

from backend.app.api.endpoints import auth, accounts

# Initialize the main API router
api_router = APIRouter()

# Include the endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])