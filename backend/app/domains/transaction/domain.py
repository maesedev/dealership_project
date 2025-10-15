"""
Dominio Transaction - Lógica de negocio pura para transacciones.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from enum import Enum


class OperationType(str, Enum):
    """Tipos de operación para transacciones"""
    IN = "CASH IN"
    OUT = "CASH OUT"


class TransactionMedia(str, Enum):
    """Medios de transacción"""
    DIGITAL = "DIGITAL"
    CASH = "CASH"


class TransactionDomain(BaseModel):
    """
    Entidad de dominio Transaction.
    Representa una transacción financiera del sistema.
    """
    id: Optional[str] = None
    user_id: str
    session_id: str
    cantidad: int
    operation_type: OperationType
    transaction_media: TransactionMedia
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('cantidad')
    def validate_cantidad(cls, v):
        """Validar que la cantidad sea positiva"""
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v
    
    def get_signed_amount(self) -> int:
        """Obtener la cantidad con signo según el tipo de operación"""
        return self.cantidad if self.operation_type == OperationType.IN else -self.cantidad
    
    def is_income(self) -> bool:
        """Verificar si es una transacción de ingreso"""
        return self.operation_type == OperationType.IN
    
    def is_expense(self) -> bool:
        """Verificar si es una transacción de egreso"""
        return self.operation_type == OperationType.OUT
    
    def is_digital(self) -> bool:
        """Verificar si es una transacción digital"""
        return self.transaction_media == TransactionMedia.DIGITAL
    
    def is_cash(self) -> bool:
        """Verificar si es una transacción en efectivo"""
        return self.transaction_media == TransactionMedia.CASH
    
    def validate_business_rules(self) -> list[str]:
        """
        Validar reglas de negocio de la transacción.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar user_id
        if not self.user_id or len(self.user_id.strip()) == 0:
            errors.append("El user_id es obligatorio")
        
        # Validar session_id
        if not self.session_id or len(self.session_id.strip()) == 0:
            errors.append("El session_id es obligatorio")
        
        # Validar cantidad
        if self.cantidad <= 0:
            errors.append("La cantidad debe ser mayor a 0")
        
        # Validar operation_type
        if self.operation_type not in [OperationType.IN, OperationType.OUT]:
            errors.append("El tipo de operación debe ser CASH IN o CASH OUT")
        
        # Validar transaction_media
        if self.transaction_media not in [TransactionMedia.DIGITAL, TransactionMedia.CASH]:
            errors.append("El medio de transacción debe ser DIGITAL o CASH")
        
        return errors


class TransactionDomainService:
    """
    Servicio de dominio para Transaction.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_transaction(user_id: str, session_id: str, cantidad: int,
                          operation_type: OperationType, transaction_media: TransactionMedia,
                          comment: str = None) -> TransactionDomain:
        """
        Crear una nueva transacción con validación de reglas de negocio.
        """
        transaction = TransactionDomain(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=operation_type,
            transaction_media=transaction_media,
            comment=comment,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Validar reglas de negocio
        errors = transaction.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return transaction
    
    @staticmethod
    def create_income(user_id: str, session_id: str, cantidad: int,
                     transaction_media: TransactionMedia, comment: str = None) -> TransactionDomain:
        """
        Crear una transacción de ingreso.
        """
        return TransactionDomainService.create_transaction(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=OperationType.IN,
            transaction_media=transaction_media,
            comment=comment
        )
    
    @staticmethod
    def create_expense(user_id: str, session_id: str, cantidad: int,
                      transaction_media: TransactionMedia, comment: str = None) -> TransactionDomain:
        """
        Crear una transacción de egreso.
        """
        return TransactionDomainService.create_transaction(
            user_id=user_id,
            session_id=session_id,
            cantidad=cantidad,
            operation_type=OperationType.OUT,
            transaction_media=transaction_media,
            comment=comment
        )

