"""
Endpoints para la gestión de bonos.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.bono_service.service import BonoService
from app.services.user_service.service import UserService
from app.services.session_service.service import SessionService
from app.shared.schemas.bono_schemas import (
    BonoCreateSchema,
    BonoUpdateSchema,
    BonoResponseSchema,
    BonoListResponseSchema
)
from app.domains.user.domain import UserDomain, UserRole
from app.shared.dependencies.auth import (
    get_current_active_user,
    get_current_dealer_or_higher
)
from app.shared.dependencies.services import (
    get_bono_service,
    get_user_service,
    get_session_service
)

# Crear router para bonos
router = APIRouter()


@router.post("/", response_model=BonoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_bono(
    bono_data: BonoCreateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    bono_service: BonoService = Depends(get_bono_service),
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Crear un nuevo bono.
    
    Permisos:
    - Solo Dealers, Managers y Admins pueden crear bonos
    
    Validaciones:
    - El user_id debe existir en la base de datos
    - El session_id debe existir en la base de datos
    """
    try:
        # Verificar que el usuario existe
        user = await user_service.get_user_by_id(bono_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {bono_data.user_id} no encontrado"
            )
        
        # Verificar que la sesión existe
        session = await session_service.get_session_by_id(bono_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {bono_data.session_id} no encontrada"
            )
        
        # Verificar que la sesión esté activa (abierta)
        if not session.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede registrar un bono en una sesión que ya finalizó"
            )
        
        bono = await bono_service.create_bono(
            user_id=bono_data.user_id,
            session_id=bono_data.session_id,
            value=bono_data.value,
            comment=bono_data.comment
        )
        
        return BonoResponseSchema(**bono.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{bono_id}", response_model=BonoResponseSchema)
async def get_bono(
    bono_id: str,
    current_user: UserDomain = Depends(get_current_active_user),
    bono_service: BonoService = Depends(get_bono_service)
):
    """
    Obtener un bono por ID.
    Requiere autenticación.
    """
    bono = await bono_service.get_bono_by_id(bono_id)
    if not bono:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bono no encontrado"
        )
    
    return BonoResponseSchema(**bono.dict())


@router.get("/", response_model=BonoListResponseSchema)
async def get_bonos(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: UserDomain = Depends(get_current_active_user),
    bono_service: BonoService = Depends(get_bono_service)
):
    """
    Obtener lista de bonos con paginación.
    Opcionalmente filtrar por user_id o session_id.
    """
    if user_id:
        bonos = await bono_service.get_bonos_by_user(user_id, skip=skip, limit=limit)
    elif session_id:
        bonos = await bono_service.get_bonos_by_session(session_id, skip=skip, limit=limit)
    else:
        bonos = await bono_service.get_all_bonos(skip=skip, limit=limit)
    
    total = len(bonos)
    bono_responses = [BonoResponseSchema(**b.dict()) for b in bonos]
    
    return BonoListResponseSchema(
        bonos=bono_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.get("/session/{session_id}", response_model=BonoListResponseSchema)
async def get_bonos_by_session(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserDomain = Depends(get_current_active_user),
    bono_service: BonoService = Depends(get_bono_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener todos los bonos de una sesión específica.
    
    Permisos:
    - Cualquier usuario autenticado puede consultar bonos
    
    Args:
        session_id: ID de la sesión
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
    
    Returns:
        Lista de bonos de la sesión ordenados por fecha de creación (más recientes primero)
    """
    # Verificar que la sesión existe
    session = await session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión con ID {session_id} no encontrada"
        )
    
    bonos = await bono_service.get_bonos_by_session(session_id, skip=skip, limit=limit)
    total = len(bonos)
    bono_responses = [BonoResponseSchema(**b.dict()) for b in bonos]
    
    return BonoListResponseSchema(
        bonos=bono_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.put("/{bono_id}", response_model=BonoResponseSchema)
async def update_bono(
    bono_id: str,
    bono_data: BonoUpdateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    bono_service: BonoService = Depends(get_bono_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Actualizar un bono.
    Solo Dealers, Managers y Admins pueden actualizar bonos.
    
    Campos actualizables:
    - value
    - comment
    
    Nota: Los campos user_id y session_id NO se pueden modificar una vez creado el bono.
    
    Restricciones adicionales:
    - Si la sesión está terminada (cerrada), solo Managers y Admins pueden modificar el bono
    - Dealers NO pueden modificar bonos de sesiones cerradas
    """
    try:
        # Obtener el bono actual para verificar la sesión
        existing_bono = await bono_service.get_bono_by_id(bono_id)
        if not existing_bono:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bono no encontrado"
            )
        
        # Obtener la sesión asociada al bono
        session = await session_service.get_session_by_id(existing_bono.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {existing_bono.session_id} no encontrada"
            )
        
        # Verificar si la sesión está terminada (tiene end_time)
        if session.end_time is not None:
            # Si la sesión está cerrada, solo Managers y Admins pueden modificar
            is_manager_or_admin = (
                UserRole.MANAGER in current_user.roles or 
                UserRole.ADMIN in current_user.roles
            )
            
            if not is_manager_or_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes modificar bonos de sesiones cerradas. Solo Managers y Admins pueden hacerlo."
                )
        
        # Construir diccionario de actualizaciones
        update_dict = {}
        if bono_data.value is not None:
            update_dict["value"] = bono_data.value
        if bono_data.comment is not None:
            update_dict["comment"] = bono_data.comment
        
        bono = await bono_service.update_bono(bono_id, **update_dict)
        if not bono:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bono no encontrado"
            )
        
        return BonoResponseSchema(**bono.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{bono_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bono(
    bono_id: str,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    bono_service: BonoService = Depends(get_bono_service)
):
    """
    Eliminar un bono.
    Solo Dealers, Managers y Admins pueden eliminar bonos.
    """
    success = await bono_service.delete_bono(bono_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bono no encontrado"
        )
    
    return None



