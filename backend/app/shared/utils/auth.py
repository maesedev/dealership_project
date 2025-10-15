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
        
        print("\n" + "="*60)
        print("🔐 [DEBUG] Creando nuevo token JWT...")
        print(f"Hora actual (UTC): {now}")
        print(f"Expiración (UTC): {expire}")
        print(f"Duración (minutos): {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        print(f"Usuario: {data.get('username', 'N/A')}")
        print("="*60 + "\n")
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verificar y decodificar un token JWT.
        """
        print("\n" + "="*60)
        print("🔍 [DEBUG] Verificando token JWT...")
        print(f"Token (primeros 50 chars): {token[:50]}...")
        print(f"Timestamp actual (UTC): {datetime.now(timezone.utc)}")
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print("✅ [DEBUG] Token decodificado exitosamente")
            print(f"Payload: {payload}")
            
            # Verificar expiración manualmente
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                print(f"Expiración del token: {exp_datetime}")
                print(f"Hora actual (UTC): {now}")
                print(f"Diferencia (segundos): {(exp_datetime - now).total_seconds()}")
                
                if now > exp_datetime:
                    print("❌ [DEBUG] Token EXPIRADO según verificación manual")
                else:
                    print("✅ [DEBUG] Token AÚN VÁLIDO según verificación manual")
            
            print("="*60 + "\n")
            return payload
        except JWTError as e:
            print(f"❌ [DEBUG] Error al decodificar token: {type(e).__name__}")
            print(f"Mensaje de error: {str(e)}")
            print("="*60 + "\n")
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
