"""
Dependencias de autenticación para FastAPI.
Estas funciones se usan como dependencias en los endpoints protegidos.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domains.user.domain import UserDomain, UserRole
from app.services.auth_service.service import AuthService


# Configurar el esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserDomain:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    
    Args:
        credentials: Credenciales Bearer del header Authorization
    
    Returns:
        UserDomain del usuario autenticado
    
    Raises:
        HTTPException: 401 si el token es inválido o el usuario no existe
    """
    auth_service = AuthService()
    
    # Extraer el token
    token = credentials.credentials
    
    # Obtener usuario desde el token
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: UserDomain = Depends(get_current_user)
) -> UserDomain:
    """
    Dependencia para verificar que el usuario esté activo.
    
    Args:
        current_user: Usuario obtenido del token
    
    Returns:
        UserDomain si el usuario está activo
    
    Raises:
        HTTPException: 403 si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return current_user


class RoleChecker:
    """
    Clase para crear dependencias que verifican roles específicos.
    
    Ejemplo de uso:
        @router.get("/admin", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
    """
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: UserDomain = Depends(get_current_active_user)
    ) -> UserDomain:
        """
        Verificar que el usuario tenga al menos uno de los roles permitidos.
        
        Args:
            current_user: Usuario actual autenticado
        
        Returns:
            UserDomain si tiene permisos
        
        Raises:
            HTTPException: 403 si no tiene los roles requeridos
        """
        # Verificar si el usuario tiene al menos uno de los roles permitidos
        has_permission = any(
            role in current_user.roles 
            for role in self.allowed_roles
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los siguientes roles: {[role.value for role in self.allowed_roles]}"
            )
        
        return current_user


# Dependencias predefinidas para roles comunes
require_admin = RoleChecker([UserRole.ADMIN])
require_dealer = RoleChecker([UserRole.DEALER, UserRole.ADMIN])
require_manager = RoleChecker([UserRole.MANAGER, UserRole.ADMIN])

