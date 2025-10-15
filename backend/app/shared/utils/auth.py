"""
Utilidades de autenticación y autorización.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings


class AuthUtils:
    """Utilidades para autenticación JWT"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear un token de acceso JWT.
        Utiliza UTC para evitar problemas de zona horaria.
        """
        to_encode = data.copy()
        
        # Usar datetime con timezone UTC explícito para evitar problemas de zona horaria
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verificar y decodificar un token JWT.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_token_expiration(token: str) -> Optional[datetime]:
        """
        Obtener la fecha de expiración de un token.
        Retorna el datetime en UTC.
        """
        payload = AuthUtils.verify_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        return None
