"""
Schemas Pydantic para la entidad Transaction.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator
from app.domains.transaction.domain import OperationType, TransactionMedia


class TransactionCreateSchema(BaseModel):
    """Schema para crear una transacción"""
    user_id: str
    session_id: str
    cantidad: int
    operation_type: OperationType
    transaction_media: TransactionMedia
    comment: Optional[str] = None
    
    @field_validator('user_id', 'session_id')
    def validate_ids(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Los IDs son obligatorios')
        return v.strip()
    
    @field_validator('cantidad')
    def validate_cantidad(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v


class TransactionUpdateSchema(BaseModel):
    """Schema para actualizar una transacción"""
    cantidad: Optional[int] = None
    operation_type: Optional[OperationType] = None
    transaction_media: Optional[TransactionMedia] = None
    comment: Optional[str] = None
    
    @field_validator('cantidad')
    def validate_cantidad(cls, v):
        if v is not None and v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v


class TransactionResponseSchema(BaseModel):
    """Schema para respuesta de transacción"""
    id: str
    user_id: str
    session_id: str
    cantidad: int
    operation_type: OperationType
    transaction_media: TransactionMedia
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    signed_amount: Optional[int] = None
    
    @model_validator(mode='after')
    def calculate_signed_amount(self):
        """Calcular signed_amount si no está presente"""
        if self.signed_amount is None:
            # CASH IN es positivo, CASH OUT es negativo
            if self.operation_type == OperationType.IN:
                self.signed_amount = self.cantidad
            else:
                self.signed_amount = -self.cantidad
        return self
    
    class Config:
        from_attributes = True


class TransactionListResponseSchema(BaseModel):
    """Schema para respuesta de lista de transacciones"""
    transactions: List[TransactionResponseSchema]
    total: int
    page: int
    limit: int


class TransactionStatsSchema(BaseModel):
    """Schema para estadísticas de transacciones"""
    total_transactions: int
    total_income: int
    total_expenses: int
    net_balance: int
    digital_transactions: int
    cash_transactions: int
    income_by_media: dict
    expenses_by_media: dict


class TransactionFilterSchema(BaseModel):
    """Schema para filtrar transacciones"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation_type: Optional[OperationType] = None
    transaction_media: Optional[TransactionMedia] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

