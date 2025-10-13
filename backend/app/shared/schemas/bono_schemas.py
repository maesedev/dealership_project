"""
Schemas Pydantic para la entidad Bono.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class BonoCreateSchema(BaseModel):
    """Schema para crear un bono"""
    user_id: str
    session_id: str
    value: int
    comment: Optional[str] = None
    
    @field_validator('user_id', 'session_id')
    def validate_ids(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Los IDs son obligatorios')
        return v.strip()
    
    @field_validator('value')
    def validate_value(cls, v):
        if v <= 0:
            raise ValueError('El valor del bono debe ser mayor a 0')
        return v


class BonoUpdateSchema(BaseModel):
    """Schema para actualizar un bono"""
    value: Optional[int] = None
    comment: Optional[str] = None
    
    @field_validator('value')
    def validate_value(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El valor del bono debe ser mayor a 0')
        return v


class BonoResponseSchema(BaseModel):
    """Schema para respuesta de bono"""
    id: str
    user_id: str
    session_id: str
    value: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BonoListResponseSchema(BaseModel):
    """Schema para respuesta de lista de bonos"""
    bonos: List[BonoResponseSchema]
    total: int
    page: int
    limit: int


class BonoStatsSchema(BaseModel):
    """Schema para estadísticas de bonos"""
    total_bonos: int
    total_value: int
    average_value: float
    max_bono: Optional[dict] = None
    min_bono: Optional[dict] = None
    bonos_by_user: dict
    bonos_by_session: dict


class BonoFilterSchema(BaseModel):
    """Schema para filtrar bonos"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

