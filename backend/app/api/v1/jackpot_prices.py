"""
Endpoints para la gestión de premios jackpot.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.jackpot_price_service.service import JackpotPriceService
from app.services.user_service.service import UserService
from app.services.session_service.service import SessionService
from app.shared.schemas.jackpot_price_schemas import (
    JackpotPriceCreateSchema,
    JackpotPriceUpdateSchema,
    JackpotPriceResponseSchema,
    JackpotPriceListResponseSchema
)
from app.domains.user.domain import UserDomain, UserRole
from app.shared.dependencies.auth import (
    get_current_active_user,
    get_current_dealer_or_higher
)
from app.shared.dependencies.services import (
    get_jackpot_price_service,
    get_user_service,
    get_session_service
)

# Crear router para jackpot prices
router = APIRouter()


@router.post("/", response_model=JackpotPriceResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_jackpot_price(
    jackpot_data: JackpotPriceCreateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service),
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Crear un nuevo premio jackpot.
    
    Permisos:
    - Solo Dealers, Managers y Admins pueden crear premios jackpot
    
    Validaciones:
    - El user_id debe existir en la base de datos
    - El session_id debe existir en la base de datos
    """
    try:
        # Verificar que el usuario existe
        user = await user_service.get_user_by_id(jackpot_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {jackpot_data.user_id} no encontrado"
            )
        
        # Verificar que la sesión existe
        session = await session_service.get_session_by_id(jackpot_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {jackpot_data.session_id} no encontrada"
            )
        
        # Verificar que la sesión esté activa (abierta)
        if not session.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede registrar un premio jackpot en una sesión que ya finalizó"
            )
        
        jackpot = await jackpot_price_service.create_jackpot_price(
            user_id=jackpot_data.user_id,
            session_id=jackpot_data.session_id,
            value=jackpot_data.value,
            winner_hand=jackpot_data.winner_hand,
            comment=jackpot_data.comment
        )
        
        return JackpotPriceResponseSchema(**jackpot.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{jackpot_id}", response_model=JackpotPriceResponseSchema)
async def get_jackpot_price(
    jackpot_id: str,
    current_user: UserDomain = Depends(get_current_active_user),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service)
):
    """
    Obtener un premio jackpot por ID.
    Requiere autenticación.
    """
    jackpot = await jackpot_price_service.get_jackpot_price_by_id(jackpot_id)
    if not jackpot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premio jackpot no encontrado"
        )
    
    return JackpotPriceResponseSchema(**jackpot.dict())


@router.get("/", response_model=JackpotPriceListResponseSchema)
async def get_jackpot_prices(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: UserDomain = Depends(get_current_active_user),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service)
):
    """
    Obtener lista de premios jackpot con paginación.
    Opcionalmente filtrar por user_id o session_id.
    """
    if user_id:
        jackpots = await jackpot_price_service.get_jackpots_by_user(user_id, skip=skip, limit=limit)
    elif session_id:
        jackpots = await jackpot_price_service.get_jackpots_by_session(session_id, skip=skip, limit=limit)
    else:
        jackpots = await jackpot_price_service.get_all_jackpots(skip=skip, limit=limit)
    
    total = len(jackpots)
    jackpot_responses = [JackpotPriceResponseSchema(**j.dict()) for j in jackpots]
    
    return JackpotPriceListResponseSchema(
        jackpots=jackpot_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.get("/top/winners", response_model=JackpotPriceListResponseSchema)
async def get_top_jackpot_winners(
    limit: int = 10,
    threshold: int = 0,
    current_user: UserDomain = Depends(get_current_active_user),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service)
):
    """
    Obtener los top ganadores de jackpot (ordenados por valor descendente).
    """
    jackpots = await jackpot_price_service.get_high_value_jackpots(threshold=threshold, skip=0, limit=limit)
    total = len(jackpots)
    jackpot_responses = [JackpotPriceResponseSchema(**j.dict()) for j in jackpots]
    
    return JackpotPriceListResponseSchema(
        jackpots=jackpot_responses,
        total=total,
        page=1,
        limit=limit
    )


@router.put("/{jackpot_id}", response_model=JackpotPriceResponseSchema)
async def update_jackpot_price(
    jackpot_id: str,
    jackpot_data: JackpotPriceUpdateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service),
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Actualizar un premio jackpot.
    Solo Dealers, Managers y Admins pueden actualizar premios jackpot.
    
    Validaciones:
    - Si se actualiza user_id, debe existir en la base de datos
    - Si se actualiza session_id, debe existir en la base de datos
    
    Restricciones adicionales:
    - Si la sesión está terminada (cerrada), solo Managers y Admins pueden modificar el premio
    - Dealers NO pueden modificar premios jackpot de sesiones cerradas
    """
    try:
        # Obtener el premio jackpot actual para verificar la sesión
        existing_jackpot = await jackpot_price_service.get_jackpot_price_by_id(jackpot_id)
        if not existing_jackpot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Premio jackpot no encontrado"
            )
        
        # Obtener la sesión asociada al premio jackpot
        session = await session_service.get_session_by_id(existing_jackpot.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {existing_jackpot.session_id} no encontrada"
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
                    detail="No puedes modificar premios jackpot de sesiones cerradas. Solo Managers y Admins pueden hacerlo."
                )
        
        # Si se actualiza user_id, verificar que existe
        if jackpot_data.user_id is not None:
            user = await user_service.get_user_by_id(jackpot_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario con ID {jackpot_data.user_id} no encontrado"
                )
        
        # Si se actualiza session_id, verificar que existe
        if jackpot_data.session_id is not None:
            new_session = await session_service.get_session_by_id(jackpot_data.session_id)
            if not new_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sesión con ID {jackpot_data.session_id} no encontrada"
                )
        
        # Construir diccionario de actualizaciones
        update_dict = {}
        if jackpot_data.user_id is not None:
            update_dict["user_id"] = jackpot_data.user_id
        if jackpot_data.session_id is not None:
            update_dict["session_id"] = jackpot_data.session_id
        if jackpot_data.value is not None:
            update_dict["value"] = jackpot_data.value
        if jackpot_data.winner_hand is not None:
            update_dict["winner_hand"] = jackpot_data.winner_hand
        if jackpot_data.comment is not None:
            update_dict["comment"] = jackpot_data.comment
        
        jackpot = await jackpot_price_service.update_jackpot_price(jackpot_id, **update_dict)
        if not jackpot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Premio jackpot no encontrado"
            )
        
        return JackpotPriceResponseSchema(**jackpot.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{jackpot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jackpot_price(
    jackpot_id: str,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    jackpot_price_service: JackpotPriceService = Depends(get_jackpot_price_service)
):
    """
    Eliminar un premio jackpot.
    Solo Dealers, Managers y Admins pueden eliminar premios jackpot.
    """
    success = await jackpot_price_service.delete_jackpot(jackpot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Premio jackpot no encontrado"
        )
    
    return None



