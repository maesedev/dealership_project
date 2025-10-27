"""
Aplicación principal FastAPI para el sistema de concesionario.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.infrastructure.database.connection import connect_to_mongo, close_mongo_connection
from app.api.v1.router import api_router
from app.shared.utils.logger import get_logger

# Logger para la aplicación principal
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejo del ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la aplicación.
    """
    # Startup: Conectar a MongoDB
    logger.info("🚀 Iniciando aplicación FastAPI...")
    await connect_to_mongo()
    logger.info("✅ Aplicación iniciada correctamente")
    yield
    # Shutdown: Cerrar conexión a MongoDB
    logger.info("🛑 Cerrando aplicación...")
    await close_mongo_connection()
    logger.info("✅ Aplicación cerrada correctamente")


# Crear instancia de FastAPI
app = FastAPI(
    title="Dealership API",
    description="API para sistema de concesionario de vehículos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
