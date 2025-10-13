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
from app.domains.user.domain import UserRole

# Crear router para usuarios
router = APIRouter()

# Instancia del servicio
user_service = UserService()


@router.post("/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateSchema):
    """
    Crear un nuevo usuario.
    """
    try:
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            roles=user_data.roles
        )
        return UserResponseSchema(**user.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(user_id: str):
    """
    Obtener un usuario por ID.
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.get("/", response_model=UserListResponseSchema)
async def get_users(skip: int = 0, limit: int = 100):
    """
    Obtener lista de usuarios con paginación.
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
async def update_user(user_id: str, user_data: UserUpdateSchema):
    """
    Actualizar un usuario.
    """
    # Convertir el schema a diccionario, excluyendo valores None
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay datos para actualizar")
    
    user = await user_service.update_user(user_id, **update_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.put("/{user_id}/roles", response_model=UserResponseSchema)
async def update_user_roles(user_id: str, roles_data: UserRoleUpdateSchema):
    """
    Actualizar roles de un usuario.
    """
    user = await user_service.update_user_roles(user_id, roles_data.roles)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.post("/{user_id}/activate", response_model=UserResponseSchema)
async def activate_user(user_id: str):
    """
    Activar un usuario.
    """
    user = await user_service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.post("/{user_id}/deactivate", response_model=UserResponseSchema)
async def deactivate_user(user_id: str):
    """
    Desactivar un usuario.
    """
    user = await user_service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return UserResponseSchema(**user.dict())


@router.get("/stats/overview", response_model=UserStatsSchema)
async def get_user_stats():
    """
    Obtener estadísticas de usuarios.
    """
    stats = await user_service.get_user_stats()
    return UserStatsSchema(**stats)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """
    Eliminar un usuario.
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
