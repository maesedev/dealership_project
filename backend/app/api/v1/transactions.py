"""
Endpoints para la gestión de transacciones.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from app.services.transaction_service.service import TransactionService
from app.services.user_service.service import UserService
from app.services.session_service.service import SessionService
from app.shared.schemas.transaction_schemas import (
    TransactionCreateSchema,
    TransactionUpdateSchema,
    TransactionResponseSchema,
    TransactionListResponseSchema
)
from app.domains.user.domain import UserDomain, UserRole
from app.shared.dependencies.auth import (
    get_current_active_user,
    get_current_dealer_or_higher
)
from app.shared.dependencies.services import (
    get_transaction_service,
    get_user_service,
    get_session_service
)

# Crear router para transacciones
router = APIRouter()


@router.post("/", response_model=TransactionResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreateSchema,
    current_user: UserDomain = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Crear una nueva transacción.
    
    Validaciones:
    - El user_id debe existir en la base de datos
    - El session_id debe existir en la base de datos
    """
    try:
        # Verificar que el usuario existe
        user = await user_service.get_user_by_id(transaction_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {transaction_data.user_id} no encontrado"
            )
        
        # Verificar que la sesión existe
        session = await session_service.get_session_by_id(transaction_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {transaction_data.session_id} no encontrada"
            )
        
        # Verificar que la sesión esté activa (abierta)
        if not session.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede registrar una transacción en una sesión que ya finalizó"
            )
        
        transaction = await transaction_service.create_transaction(
            user_id=transaction_data.user_id,
            session_id=transaction_data.session_id,
            cantidad=transaction_data.cantidad,
            operation_type=transaction_data.operation_type,
            transaction_media=transaction_data.transaction_media,
            comment=transaction_data.comment
        )
        
        return TransactionResponseSchema(**transaction.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionResponseSchema)
async def get_transaction(
    transaction_id: str,
    current_user: UserDomain = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Obtener una transacción por ID.
    Requiere autenticación.
    """
    transaction = await transaction_service.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    return TransactionResponseSchema(**transaction.dict())


@router.get("/", response_model=TransactionListResponseSchema)
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: UserDomain = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Obtener lista de transacciones con paginación.
    Opcionalmente filtrar por user_id o session_id.
    """
    if user_id:
        transactions = await transaction_service.get_transactions_by_user(user_id, skip=skip, limit=limit)
    elif session_id:
        transactions = await transaction_service.get_transactions_by_session(session_id, skip=skip, limit=limit)
    else:
        transactions = await transaction_service.get_all_transactions(skip=skip, limit=limit)
    
    total = len(transactions)
    transaction_responses = [TransactionResponseSchema(**t.dict()) for t in transactions]
    
    return TransactionListResponseSchema(
        transactions=transaction_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.get("/session/{session_id}", response_model=TransactionListResponseSchema)
async def get_transactions_by_session(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserDomain = Depends(get_current_active_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Obtener todas las transacciones de una sesión específica.
    
    Permisos:
    - Cualquier usuario autenticado puede consultar transacciones
    
    Args:
        session_id: ID de la sesión
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
    
    Returns:
        Lista de transacciones de la sesión ordenadas por fecha de creación (más recientes primero)
    """
    # Verificar que la sesión existe
    session = await session_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión con ID {session_id} no encontrada"
        )
    
    transactions = await transaction_service.get_transactions_by_session(session_id, skip=skip, limit=limit)
    total = len(transactions)
    transaction_responses = [TransactionResponseSchema(**t.dict()) for t in transactions]
    
    return TransactionListResponseSchema(
        transactions=transaction_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        limit=limit
    )


@router.put("/{transaction_id}", response_model=TransactionResponseSchema)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdateSchema,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    transaction_service: TransactionService = Depends(get_transaction_service),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Actualizar una transacción.
    Solo Dealers, Managers y Admins pueden actualizar transacciones.
    
    Campos actualizables:
    - cantidad
    - operation_type
    - transaction_media
    - comment
    
    Nota: Los campos user_id y session_id NO se pueden modificar una vez creada la transacción.
    
    Restricciones adicionales:
    - Si la sesión está terminada (cerrada), solo Managers y Admins pueden modificar la transacción
    - Dealers NO pueden modificar transacciones de sesiones cerradas
    """
    
    try:
        # Obtener la transacción actual para verificar la sesión
        existing_transaction = await transaction_service.get_transaction_by_id(transaction_id)
        if not existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transacción no encontrada"
            )
        
        # Obtener la sesión asociada a la transacción
        session = await session_service.get_session_by_id(existing_transaction.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión con ID {existing_transaction.session_id} no encontrada"
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
                    detail="No puedes modificar transacciones de sesiones cerradas. Solo Managers y Admins pueden hacerlo."
                )
        
        # Construir diccionario de actualizaciones
        update_dict = {}
        if transaction_data.cantidad is not None:
            update_dict["cantidad"] = transaction_data.cantidad
        if transaction_data.operation_type is not None:
            update_dict["operation_type"] = transaction_data.operation_type
        if transaction_data.transaction_media is not None:
            update_dict["transaction_media"] = transaction_data.transaction_media
        if transaction_data.comment is not None:
            update_dict["comment"] = transaction_data.comment
        
        transaction = await transaction_service.update_transaction(transaction_id, **update_dict)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transacción no encontrada"
            )
        
        return TransactionResponseSchema(**transaction.dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: UserDomain = Depends(get_current_dealer_or_higher),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """
    Eliminar una transacción.
    Solo Dealers, Managers y Admins pueden eliminar transacciones.
    """
    success = await transaction_service.delete_transaction(transaction_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    return None



