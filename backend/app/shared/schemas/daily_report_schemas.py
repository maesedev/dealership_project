"""
Schemas Pydantic para la entidad DailyReport.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, field_validator


class JackpotWinEntrySchema(BaseModel):
    """Schema para entrada de jackpot ganado"""
    jackpot_win_id: str
    sum: int


class BonoEntrySchema(BaseModel):
    """Schema para entrada de bono otorgado"""
    bono_id: str
    sum: int


class DailyReportCreateSchema(BaseModel):
    """Schema para crear un reporte diario"""
    date: date
    reik: int = 0
    jackpot: int = 0
    ganancias: int = 0
    gastos: int = 0
    sessions: Optional[List[str]] = []
    jackpot_wins: Optional[List[JackpotWinEntrySchema]] = []
    bonos: Optional[List[BonoEntrySchema]] = []
    comment: Optional[str] = None
    
    @field_validator('date')
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError('La fecha no puede ser futura')
        return v
    
    @field_validator('reik', 'jackpot', 'ganancias', 'gastos')
    def validate_positive_values(cls, v):
        if v < 0:
            raise ValueError('Los valores monetarios no pueden ser negativos')
        return v


class DailyReportUpdateSchema(BaseModel):
    """Schema para actualizar un reporte diario"""
    reik: Optional[int] = None
    jackpot: Optional[int] = None
    ganancias: Optional[int] = None
    gastos: Optional[int] = None
    sessions: Optional[List[str]] = None
    jackpot_wins: Optional[List[JackpotWinEntrySchema]] = None
    bonos: Optional[List[BonoEntrySchema]] = None
    comment: Optional[str] = None
    
    @field_validator('reik', 'jackpot', 'ganancias', 'gastos')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Los valores monetarios no pueden ser negativos')
        return v


class DailyReportResponseSchema(BaseModel):
    """Schema para respuesta de reporte diario"""
    id: str
    date: date
    reik: int
    jackpot: int
    ganancias: int
    gastos: int
    sessions: Optional[List[str]] = []
    jackpot_wins: Optional[List[JackpotWinEntrySchema]] = []
    bonos: Optional[List[BonoEntrySchema]] = []
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    net_profit: int
    total_income: int
    is_profitable: bool
    profit_margin: float
    
    class Config:
        from_attributes = True


class DailyReportListResponseSchema(BaseModel):
    """Schema para respuesta de lista de reportes diarios"""
    reports: List[DailyReportResponseSchema]
    total: int
    page: int
    limit: int


class DailyReportStatsSchema(BaseModel):
    """Schema para estadísticas de reportes diarios"""
    total_reports: int
    total_reik: int
    total_jackpot: int
    total_ganancias: int
    total_gastos: int
    total_net_profit: int
    average_daily_profit: float
    profitable_days: int
    unprofitable_days: int
    best_day: Optional[dict] = None
    worst_day: Optional[dict] = None


class DailyReportFilterSchema(BaseModel):
    """Schema para filtrar reportes diarios"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_profit: Optional[int] = None
    max_profit: Optional[int] = None
    is_profitable: Optional[bool] = None

