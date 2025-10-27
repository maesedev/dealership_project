"""
Endpoints de autenticación.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.shared.schemas.user_schemas import UserLoginSchema, TokenResponseSchema
from app.services.auth_service.service import AuthService
from app.shared.dependencies.auth import get_current_active_user
from app.shared.dependencies.services import get_auth_service
from app.domains.user.domain import UserDomain


router = APIRouter()


@router.post("/login", response_model=TokenResponseSchema, status_code=status.HTTP_200_OK)
async def login(
    credentials: UserLoginSchema,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint de autenticación - Login con username y contraseña.
    
    Este endpoint recibe las credenciales del usuario y devuelve un JWT
    si las credenciales son válidas.
    
    **Respuestas:**
    - 200: Login exitoso, devuelve el token JWT y datos del usuario
    - 401: Credenciales inválidas o usuario no activo
    
    **Ejemplo de respuesta:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": "507f1f77bcf86cd799439011",
            "username": "johndoe",
            "name": "John Doe",
            "roles": ["USER"],
            "is_active": true,
            "created_at": "2025-01-06T21:00:00Z",
            "updated_at": "2025-01-06T21:00:00Z",
            "security": {
                "failed_attempts": 0
            }
        }
    }
    ```
    """
    
    # Intentar autenticar (convertir username a minúsculas)
    result = await auth_service.login(
        username=credentials.username.lower(),
        password=credentials.password
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o cuenta bloqueada. Verifica tu username y contraseña.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convertir UserDomain a UserResponseSchema
    from app.shared.schemas.user_schemas import UserResponseSchema, UserSecuritySchema
    
    user_response = UserResponseSchema(
        id=result["user"].id,
        username=result["user"].username,
        name=result["user"].name,
        roles=result["user"].roles,
        is_active=result["user"].is_active,
        created_at=result["user"].created_at,
        updated_at=result["user"].updated_at,
        security=UserSecuritySchema(
            failed_attempts=result["user"].security.failed_attempts
        )
    )
    
    return TokenResponseSchema(
        access_token=result["access_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
        user=user_response
    )


@router.post("/refresh", response_model=TokenResponseSchema, status_code=status.HTTP_200_OK)
async def refresh_token(current_user: UserDomain = Depends(get_current_active_user)):
    """
    Refrescar el token JWT del usuario autenticado.
    
    Este endpoint genera un nuevo token JWT para el usuario que ya está autenticado.
    Requiere enviar el token actual en el header Authorization.
    
    **Headers requeridos:**
    - Authorization: Bearer {token_actual}
    
    **Respuestas:**
    - 200: Token refrescado exitosamente
    - 401: Token inválido o expirado
    - 403: Usuario inactivo
    """
    # Generar nuevo token directamente usando los datos del usuario actual
    from datetime import timedelta
    from app.core.config import settings
    from app.shared.utils.auth import AuthUtils
    
    token_data = {
        "sub": current_user.id,
        "username": current_user.username,
        "roles": [role.value for role in current_user.roles],
        "name": current_user.name
    }
    
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthUtils.create_access_token(
        data=token_data,
        expires_delta=expires_delta
    )
    
    # Convertir UserDomain a UserResponseSchema
    from app.shared.schemas.user_schemas import UserResponseSchema, UserSecuritySchema
    
    user_response = UserResponseSchema(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        roles=current_user.roles,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        security=UserSecuritySchema(
            failed_attempts=current_user.security.failed_attempts
        )
    )
    
    return TokenResponseSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response
    )


@router.get("/me", response_model=dict, status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: UserDomain = Depends(get_current_active_user)):
    """
    Obtener información del usuario autenticado actual.
    
    Este endpoint devuelve los datos del usuario que está autenticado con el token JWT.
    
    **Headers requeridos:**
    - Authorization: Bearer {token}
    
    **Respuestas:**
    - 200: Información del usuario
    - 401: Token inválido o expirado
    - 403: Usuario inactivo
    """
    from app.shared.schemas.user_schemas import UserResponseSchema, UserSecuritySchema
    
    user_response = UserResponseSchema(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        roles=current_user.roles,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        security=UserSecuritySchema(
            failed_attempts=current_user.security.failed_attempts
        )
    )
    
    return {
        "user": user_response,
        "message": "Usuario autenticado correctamente"
    }

