from fastapi import APIRouter
from app.api import auth, recommendations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
