"""
Configuración de la aplicación.
"""
import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Configuración de la aplicación
    APP_NAME: str = "Dealership API"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Configuración de MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "dealership_db"
    
    # Configuración de CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Configuración de seguridad
    SECRET_KEY: str = "tu-clave-secreta-aqui-cambiar-en-produccion"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
