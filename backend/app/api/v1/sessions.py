"""
Endpoints para la gestión de sesiones.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.session_service.service import SessionService
from app.services.user_service.service import UserService
from app.shared.schemas.session_schemas import (
    SessionCreateSchema,
    SessionUpdateSchema,
    SessionResponseSchema,
    SessionListResponseSchema
)
from app.domains.user.domain import UserRole, UserDomain
from app.shared.dependencies.auth import (
    get_current_active_user,
    get_current_dealer_or_higher,
    get_current_manager_or_admin
)
from app.shared.dependencies.services import get_session_service, get_user_service

# Crear router para sesiones
router = APIRouter()


@router.post("/", response_model=SessionResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    session_service: SessionService = Depends(get_session_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Crear una nueva sesión.
    
    Permisos:
    - Dealers, Managers y Admins pueden crear sesiones
    
    Validaciones:
    - El dealer_id debe existir y ser un usuario con rol Dealer, Manager o Admin
    """
    try:
        # Verificar que el dealer existe
        dealer = await user_service.get_user_by_id(session_data.dealer_id)
        if not dealer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {session_data.dealer_id} no encontrado"
            )
        
        # Verificar que el usuario tiene rol de Dealer, Manager o Admin
        allowed_roles = [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
        if not any(role in dealer.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario debe tener rol de Dealer, Manager o Admin para iniciar una sesión"
            )
        
        session = await session_service.create_session(
            dealer_id=session_data.dealer_id,
            start_time=session_data.start_time,
            end_time=session_data.end_time,
            jackpot=session_data.jackpot,
            reik=session_data.reik,
            tips=session_data.tips,
            hourly_pay=session_data.hourly_pay,
            comment=session_data.comment
        )
        
        return SessionResponseSchema(**session.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponseSchema)
async def get_session(
    session_id: str,
    current_user: UserDomain = Depends(get_current_active_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener una sesión por ID.
    Requiere autenticación.
    """
    session = await session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )
    
    return SessionResponseSchema(**session.dict())


@router.get("/", response_model=SessionListResponseSchema)
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    dealer_id: Optional[str] = None,
    current_user: UserDomain = Depends(get_current_active_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener lista de sesiones con paginación.
    Opcionalmente filtrar por dealer_id.
    """
    if dealer_id:
        sessions = await session_service.get_sessions_by_dealer(dealer_id, skip=skip, limit=limit)
    else:
        sessions = await session_service.get_all_sessions(skip=skip, limit=limit)
    
    total = len(sessions)
    session_responses = [SessionResponseSchema(**session.dict()) for session in sessions]
    
    return SessionListResponseSchema(
        sessions=session_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.get("/active/list", response_model=SessionListResponseSchema)
async def get_active_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDomain = Depends(get_current_active_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener lista de sesiones activas (sin end_time).
    """
    sessions = await session_service.get_active_sessions(skip=skip, limit=limit)
    total = len(sessions)
    session_responses = [SessionResponseSchema(**session.dict()) for session in sessions]
    
    return SessionListResponseSchema(
        sessions=session_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.put("/{session_id}", response_model=SessionResponseSchema)
async def update_session(
    session_id: str,
    session_data: SessionUpdateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    session_service: SessionService = Depends(get_session_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Actualizar una sesión.
    
    Restricciones:
    - Solo Managers y Admins pueden actualizar hourly_pay
    - Otros campos pueden ser actualizados por Dealers, Managers o Admins
    """
    try:
        # Verificar si se está intentando actualizar hourly_pay
        if session_data.hourly_pay is not None:
            # Solo Manager o Admin puede actualizar hourly_pay
            if not (UserRole.MANAGER in current_user.roles or UserRole.ADMIN in current_user.roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo Managers y Admins pueden actualizar el hourly_pay"
                )
        
        # Si se actualiza dealer_id, verificar que existe y tiene el rol correcto
        if session_data.dealer_id is not None:
            dealer = await user_service.get_user_by_id(session_data.dealer_id)
            if not dealer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario con ID {session_data.dealer_id} no encontrado"
                )
            
            allowed_roles = [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
            if not any(role in dealer.roles for role in allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El usuario debe tener rol de Dealer, Manager o Admin"
                )
        
        # Construir diccionario de actualizaciones
        update_dict = {}
        if session_data.dealer_id is not None:
            update_dict["dealer_id"] = session_data.dealer_id
        if session_data.start_time is not None:
            update_dict["start_time"] = session_data.start_time
        if session_data.end_time is not None:
            update_dict["end_time"] = session_data.end_time
        if session_data.jackpot is not None:
            update_dict["jackpot"] = session_data.jackpot
        if session_data.reik is not None:
            update_dict["reik"] = session_data.reik
        if session_data.tips is not None:
            update_dict["tips"] = session_data.tips
        if session_data.hourly_pay is not None:
            update_dict["hourly_pay"] = session_data.hourly_pay
        if session_data.comment is not None:
            update_dict["comment"] = session_data.comment
        
        session = await session_service.update_session(session_id, **update_dict)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        return SessionResponseSchema(**session.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{session_id}/end", response_model=SessionResponseSchema)
async def end_session(
    session_id: str,
    end_time: Optional[datetime] = None,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Finalizar una sesión activa.
    Si no se proporciona end_time, se usa la hora actual.
    
    Validación:
    - No permite terminar una sesión que ya fue terminada (que ya tiene end_time)
    """
    try:
        # Verificar que la sesión existe
        existing_session = await session_service.get_session_by_id(session_id)
        if not existing_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Verificar que la sesión no haya sido terminada previamente
        if existing_session.end_time is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta sesión ya fue terminada anteriormente"
            )
        
        if end_time is None:
            end_time = datetime.utcnow()
        
        session = await session_service.end_session(session_id, end_time)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        return SessionResponseSchema(**session.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: UserDomain = Depends(get_current_manager_or_admin),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Eliminar una sesión.
    Solo Managers y Admins pueden eliminar sesiones.
    """
    success = await session_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )
    
    return None

