"""
Servicio de Autenticación - Maneja la lógica de autenticación y JWT.
Este servicio se encarga de validar credenciales y generar tokens.
"""

from datetime import timedelta
from typing import Optional
from app.domains.user.domain import UserDomain
from app.services.user_service.service import UserService
from app.shared.utils.auth import AuthUtils
from app.core.config import settings


class AuthService:
    """
    Servicio de autenticación para gestionar login y tokens JWT.
    """
    
    def __init__(self):
        self.user_service = UserService()
        self.auth_utils = AuthUtils()
    
    async def login(self, username: str, password: str) -> Optional[dict]:
        """
        Autenticar un usuario y generar un token JWT.
        
        Args:
            username: Username del usuario
            password: Contraseña del usuario
        
        Returns:
            dict con access_token, token_type, expires_in y datos del usuario
            None si las credenciales son inválidas
        """
        # Autenticar usuario usando el servicio de usuarios
        user = await self.user_service.authenticate_user(username=username, password=password)
        
        if not user:
            return None
        
        # Generar token JWT
        token_data = {
            "sub": user.id,  # Subject: ID del usuario
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "name": user.name
        }
        
        # Crear token con tiempo de expiración configurado
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.auth_utils.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # En segundos
            "user": user
        }
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verificar un token JWT y devolver el payload.
        
        Args:
            token: Token JWT a verificar
        
        Returns:
            dict con el payload del token si es válido
            None si el token es inválido o expirado
        """
        return self.auth_utils.verify_token(token)
    
    async def get_current_user(self, token: str) -> Optional[UserDomain]:
        """
        Obtener el usuario actual a partir de un token JWT.
        
        Args:
            token: Token JWT del usuario
        
        Returns:
            UserDomain si el token es válido
            None si el token es inválido o el usuario no existe
        """
        print("\n🔍 [DEBUG - AuthService] get_current_user() iniciado")
        
        payload = await self.verify_token(token)
        
        if not payload:
            print("❌ [DEBUG - AuthService] Token inválido o expirado (payload es None)")
            return None
        
        print(f"✅ [DEBUG - AuthService] Payload obtenido: {payload}")
        
        user_id = payload.get("sub")
        if not user_id:
            print("❌ [DEBUG - AuthService] No se encontró 'sub' en el payload")
            return None
        
        print(f"🔍 [DEBUG - AuthService] Buscando usuario con ID: {user_id}")
        user = await self.user_service.get_user_by_id(user_id)
        
        if not user:
            print(f"❌ [DEBUG - AuthService] Usuario con ID {user_id} no encontrado en BD")
            return None
        
        print(f"✅ [DEBUG - AuthService] Usuario encontrado: {user.username}")
        
        # Verificar que el usuario aún esté activo
        if not user.is_active:
            print(f"❌ [DEBUG - AuthService] Usuario {user.username} está INACTIVO")
            return None
        
        print(f"✅ [DEBUG - AuthService] Usuario {user.username} está ACTIVO")
        print("✅ [DEBUG - AuthService] get_current_user() completado exitosamente\n")
        return user
    
    async def refresh_token(self, old_token: str) -> Optional[dict]:
        """
        Refrescar un token JWT existente.
        
        Args:
            old_token: Token JWT actual
        
        Returns:
            dict con el nuevo access_token si el token actual es válido
            None si el token es inválido
        """
        user = await self.get_current_user(old_token)
        
        if not user:
            return None
        
        # Generar nuevo token
        token_data = {
            "sub": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "name": user.name
        }
        
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.auth_utils.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
