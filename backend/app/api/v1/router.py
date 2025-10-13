"""
Router principal de la API v1.
"""
from fastapi import APIRouter
from app.api.v1.users import router as users_router

# Crear router principal
api_router = APIRouter()

# Importar y incluir routers de cada dominio
# from app.domains.customer.routes import router as customer_router
# from app.domains.vehicle.routes import router as vehicle_router
# from app.domains.sale.routes import router as sale_router

# Incluir routers
api_router.include_router(users_router, prefix="/users", tags=["users"])
# api_router.include_router(customer_router, prefix="/customers", tags=["customers"])
# api_router.include_router(vehicle_router, prefix="/vehicles", tags=["vehicles"])
# api_router.include_router(sale_router, prefix="/sales", tags=["sales"])

@api_router.get("/health")
async def health_check():
    """Verificación de salud de la API"""
    return {"status": "healthy", "message": "API funcionando correctamente"}
