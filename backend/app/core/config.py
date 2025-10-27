"""
Configuración de la aplicación.
"""
import os
import logging
from typing import List
from pydantic_settings import BaseSettings


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
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_log_level(self) -> int:
        """Convierte el string de nivel de log a constante de logging"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.LOG_LEVEL.upper(), logging.INFO)


# Instancia global de configuración
settings = Settings()
