"""
Endpoints para la gestión de usuarios.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.user_service.service import UserService
from app.shared.schemas.user_schemas import (
    UserCreateSchema, UserResponseSchema, UserUpdateSchema,
    UserListResponseSchema, UserRoleUpdateSchema, UserStatsSchema
)
from app.domains.user.domain import UserRole, UserDomain
from app.shared.dependencies.auth import (
    get_current_active_user,
    get_current_admin,
    get_current_dealer_or_higher,
    get_current_manager_or_admin
)
from app.shared.dependencies.services import get_user_service

# Crear router para usuarios
router = APIRouter()


@router.post("/create", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    user_service: UserService = Depends(get_user_service)
):
    """
    Crear un nuevo usuario.
    
    Permisos:
    - Admins pueden crear usuarios de cualquier rol
    - Dealers pueden crear solo usuarios tipo USER
    - Managers pueden crear solo usuarios tipo USER
    
    Reglas de negocio:
    - Usuarios tipo USER: username y password opcionales, is_active = False por defecto
    - Usuarios Dealer/Manager/Admin: username y password obligatorios, is_active = True por defecto
    """
    try:
        # Validar reglas de negocio del schema
        validation_errors = user_data.validate_business_rules()
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(validation_errors)
            )
        
        # Verificar permisos según el rol a crear
        creating_privileged_role = any(
            role in [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
            for role in user_data.roles
        )
        
        # Solo Admin puede crear usuarios con roles privilegiados
        if creating_privileged_role and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden crear usuarios con roles de Dealer, Manager o Admin"
            )
        
        user = await user_service.create_user(
            username=user_data.username,
            password=user_data.password,
            name=user_data.name,
            roles=user_data.roles
        )
        return UserResponseSchema(**user.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: str,
    current_user: UserDomain = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Obtener un usuario por ID.
    Requiere autenticación.
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.get("/", response_model=UserListResponseSchema)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Obtener lista de usuarios con paginación.
    Solo Managers y Admins pueden ver la lista completa de usuarios.
    """
    users = await user_service.get_all_users(skip=skip, limit=limit)
    total = len(users)  # En una implementación real, esto vendría de un count
    
    user_responses = [UserResponseSchema(**user.dict()) for user in users]
    
    return UserListResponseSchema(
        users=user_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.put("/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: str,
    user_data: UserUpdateSchema,
    current_user: UserDomain = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Actualizar un usuario.
    Los usuarios pueden actualizarse a sí mismos, o los Admins pueden actualizar a cualquiera.
    
    RESTRICCIONES DE SEGURIDAD:
    - Los usuarios normales SOLO pueden cambiar su nombre
    - Solo Admin puede cambiar roles (usar endpoint PUT /{user_id}/roles)
    - Solo Admin puede cambiar el estado activo
    """
    # Verificar permisos: usuario puede actualizarse a sí mismo o ser Admin
    if current_user.id != user_id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario"
        )
    
    try:
        # SEGURIDAD: Verificar que no se intente cambiar roles sin ser Admin
        if user_data.roles is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los administradores pueden cambiar roles. Usa el endpoint PUT /{user_id}/roles"
                )
        
        # Actualizar campos
        update_dict = {}
        if user_data.name is not None:
            update_dict["name"] = user_data.name
        
        # Solo Admin puede cambiar el estado activo
        if user_data.is_active is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los administradores pueden cambiar el estado activo"
                )
            update_dict["is_active"] = user_data.is_active
        
        # Solo Admin puede cambiar roles (aunque idealmente debería usar el endpoint específico)
        if user_data.roles is not None:
            if UserRole.ADMIN not in current_user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los administradores pueden cambiar roles"
                )
            # Usar el método específico para cambiar roles
            await user_service.update_user_roles(user_id, user_data.roles)
        
        user = await user_service.update_user(user_id, **update_dict)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        
        return UserResponseSchema(**user.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}/roles", response_model=UserResponseSchema)
async def update_user_roles(
    user_id: str,
    role_data: UserRoleUpdateSchema,
    current_user: UserDomain = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Actualizar roles de un usuario.
    Solo administradores pueden actualizar roles.
    """
    try:
        user = await user_service.update_user_roles(user_id, role_data.roles)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        
        return UserResponseSchema(**user.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserResponseSchema)
async def activate_user(
    user_id: str,
    current_user: UserDomain = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Activar un usuario.
    Solo administradores pueden activar usuarios.
    """
    user = await user_service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.post("/{user_id}/deactivate", response_model=UserResponseSchema)
async def deactivate_user(
    user_id: str,
    current_user: UserDomain = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Desactivar un usuario.
    Solo administradores pueden desactivar usuarios.
    """
    user = await user_service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.get("/stats/overview", response_model=UserStatsSchema)
async def get_user_stats(
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Obtener estadísticas de usuarios.
    Solo Managers y Admins pueden ver estadísticas.
    """
    stats = await user_service.get_user_stats()
    return UserStatsSchema(**stats)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: UserDomain = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Eliminar un usuario.
    Solo administradores pueden eliminar usuarios.
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return None
