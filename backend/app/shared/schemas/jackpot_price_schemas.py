"""
Schemas Pydantic para la entidad JackpotPrice.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class JackpotPriceCreateSchema(BaseModel):
    """Schema para crear un premio de jackpot"""
    user_id: str
    session_id: str
    value: int
    winner_hand: Optional[str] = None
    comment: Optional[str] = None
    
    @field_validator('user_id', 'session_id')
    def validate_ids(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Los IDs son obligatorios')
        return v.strip()
    
    @field_validator('value')
    def validate_value(cls, v):
        if v <= 0:
            raise ValueError('El valor del jackpot debe ser mayor a 0')
        return v


class JackpotPriceUpdateSchema(BaseModel):
    """Schema para actualizar un premio de jackpot"""
    value: Optional[int] = None
    winner_hand: Optional[str] = None
    comment: Optional[str] = None
    
    @field_validator('value')
    def validate_value(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El valor del jackpot debe ser mayor a 0')
        return v


class JackpotPriceResponseSchema(BaseModel):
    """Schema para respuesta de premio de jackpot"""
    id: str
    user_id: str
    session_id: str
    value: int
    winner_hand: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_high_value: bool
    
    class Config:
        from_attributes = True


class JackpotPriceListResponseSchema(BaseModel):
    """Schema para respuesta de lista de premios de jackpot"""
    jackpots: List[JackpotPriceResponseSchema]
    total: int
    page: int
    limit: int


class JackpotPriceStatsSchema(BaseModel):
    """Schema para estadísticas de premios de jackpot"""
    total_jackpots: int
    total_value: int
    average_value: float
    max_jackpot: Optional[dict] = None
    min_jackpot: Optional[dict] = None
    high_value_count: int
    jackpots_by_user: dict
    jackpots_by_session: dict
    most_common_hands: dict


class JackpotPriceFilterSchema(BaseModel):
    """Schema para filtrar premios de jackpot"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    winner_hand: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

