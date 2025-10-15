"""
Router principal de la API v1.
"""
from fastapi import APIRouter
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.bonos import router as bonos_router
from app.api.v1.jackpot_prices import router as jackpot_prices_router
from app.api.v1.daily_reports import router as daily_reports_router

# Crear router principal
api_router = APIRouter()

# Incluir routers de cada dominio
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
api_router.include_router(bonos_router, prefix="/bonos", tags=["bonos"])
api_router.include_router(jackpot_prices_router, prefix="/jackpot-prices", tags=["jackpot-prices"])
api_router.include_router(daily_reports_router, prefix="/daily-reports", tags=["daily-reports"])

@api_router.get("/health")
async def health_check():
    """Verificación de salud de la API"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "API está funcionando correctamente"
    }
