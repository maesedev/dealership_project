"""
Schemas Pydantic para la entidad Session.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class SessionCreateSchema(BaseModel):
    """Schema para crear una sesión"""
    dealer_id: str
    start_time: Optional[datetime] = None
    hourly_pay: int = 0
    comment: Optional[str] = None
    
    @field_validator('dealer_id')
    def validate_dealer_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('El dealer_id es obligatorio')
        return v.strip()
    
    @field_validator('hourly_pay')
    def validate_hourly_pay(cls, v):
        if v < 0:
            raise ValueError('El pago por hora no puede ser negativo')
        return v


class SessionUpdateSchema(BaseModel):
    """Schema para actualizar una sesión"""
    end_time: Optional[datetime] = None
    jackpot: Optional[int] = None
    reik: Optional[int] = None
    tips: Optional[int] = None
    hourly_pay: Optional[int] = None
    comment: Optional[str] = None
    
    @field_validator('jackpot', 'reik', 'tips', 'hourly_pay')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Los valores monetarios no pueden ser negativos')
        return v


class SessionEndSchema(BaseModel):
    """Schema para finalizar una sesión"""
    end_time: Optional[datetime] = None


class SessionResponseSchema(BaseModel):
    """Schema para respuesta de sesión"""
    id: str
    dealer_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    jackpot: int
    reik: int
    tips: int
    hourly_pay: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    duration_hours: Optional[float] = None
    total_earnings: int
    
    class Config:
        from_attributes = True


class SessionListResponseSchema(BaseModel):
    """Schema para respuesta de lista de sesiones"""
    sessions: List[SessionResponseSchema]
    total: int
    page: int
    limit: int


class SessionStatsSchema(BaseModel):
    """Schema para estadísticas de sesiones"""
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    total_jackpot: int
    total_reik: int
    total_tips: int
    total_earnings: int
    average_duration_hours: float

