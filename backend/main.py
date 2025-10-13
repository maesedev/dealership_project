"""
Aplicación principal FastAPI para el sistema de concesionario.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.infrastructure.database.connection import connect_to_mongo, close_mongo_connection
from app.api.v1.router import api_router

# Crear instancia de FastAPI
app = FastAPI(
    title="Dealership API",
    description="API para sistema de concesionario de vehículos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def hello_world():
    """
    Ruta principal - Hello World
    """
    return {
        "message": "¡Hola! Bienvenido a la API del Concesionario",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_db_client():
    """Conectar a MongoDB al iniciar la aplicación"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    """Desconectar de MongoDB al cerrar la aplicación"""
    await close_mongo_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
