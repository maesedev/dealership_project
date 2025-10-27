"""
Dominio DailyReport - Lógica de negocio pura para reportes diarios.
"""

from typing import Optional, List, Dict
from datetime import datetime, date, timezone
from pydantic import BaseModel, field_validator
from app.shared.utils.timezone import now_bogota, bogota_to_utc


class JackpotWinEntry(BaseModel):
    """Entrada de jackpot ganado"""
    jackpot_win_id: str
    sum: int


class BonoEntry(BaseModel):
    """Entrada de bono otorgado"""
    bono_id: str
    sum: int


class DailyReportDomain(BaseModel):
    """
    Entidad de dominio DailyReport.
    Representa un reporte diario del negocio.
    """
    id: Optional[str] = None
    date: date
    reik: int = 0
    jackpot: int = 0
    ganancias: int = 0
    gastos: int = 0
    sessions: Optional[List[str]] = []
    jackpot_wins: Optional[List[JackpotWinEntry]] = []
    bonos: Optional[List[BonoEntry]] = []
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('reik', 'jackpot', 'ganancias', 'gastos')
    def validate_positive_values(cls, v):
        """Validar que los valores no sean negativos"""
        if v < 0:
            raise ValueError('Los valores monetarios no pueden ser negativos')
        return v
    
    def get_net_profit(self) -> int:
        """Calcular ganancia neta del día"""
        return self.ganancias - self.gastos
    
    def get_total_income(self) -> int:
        """Calcular total de ingresos del día"""
        return self.reik + self.jackpot + self.ganancias
    
    def is_profitable(self) -> bool:
        """Verificar si el día fue rentable"""
        return self.get_net_profit() > 0
    
    def get_profit_margin(self) -> float:
        """Calcular margen de ganancia"""
        total_income = self.get_total_income()
        if total_income == 0:
            return 0.0
        return (self.get_net_profit() / total_income) * 100
    
    def validate_business_rules(self) -> list[str]:
        """
        Validar reglas de negocio del reporte diario.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar fecha
        if not self.date:
            errors.append("La fecha es obligatoria")
        
        # Validar que la fecha no sea futura
        if self.date > date.today():
            errors.append("La fecha no puede ser futura")
        
        # Validar valores monetarios
        if self.reik < 0:
            errors.append("El reik no puede ser negativo")
        if self.jackpot < 0:
            errors.append("El jackpot no puede ser negativo")
        if self.ganancias < 0:
            errors.append("Las ganancias no pueden ser negativas")
        if self.gastos < 0:
            errors.append("Los gastos no pueden ser negativos")
        
        return errors


class DailyReportDomainService:
    """
    Servicio de dominio para DailyReport.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_daily_report(report_date: date, reik: int = 0, jackpot: int = 0,
                           ganancias: int = 0, gastos: int = 0, 
                           sessions: List[str] = None, jackpot_wins: List[JackpotWinEntry] = None,
                           bonos: List[BonoEntry] = None, comment: str = None) -> DailyReportDomain:
        """
        Crear un nuevo reporte diario con validación de reglas de negocio.
        """
        daily_report = DailyReportDomain(
            date=report_date,
            reik=reik,
            jackpot=jackpot,
            ganancias=ganancias,
            gastos=gastos,
            sessions=sessions if sessions is not None else [],
            jackpot_wins=jackpot_wins if jackpot_wins is not None else [],
            bonos=bonos if bonos is not None else [],
            comment=comment,
            created_at=bogota_to_utc(now_bogota()),
            updated_at=bogota_to_utc(now_bogota())
        )
        
        # Validar reglas de negocio
        errors = daily_report.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return daily_report
    
    @staticmethod
    def add_income(report: DailyReportDomain, amount: int, income_type: str) -> DailyReportDomain:
        """
        Agregar ingresos al reporte diario.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        if income_type == "reik":
            report.reik += amount
        elif income_type == "jackpot":
            report.jackpot += amount
        elif income_type == "ganancias":
            report.ganancias += amount
        else:
            raise ValueError("Tipo de ingreso inválido. Debe ser 'reik', 'jackpot' o 'ganancias'")
        
        report.updated_at = bogota_to_utc(now_bogota())
        return report
    
    @staticmethod
    def add_expense(report: DailyReportDomain, amount: int) -> DailyReportDomain:
        """
        Agregar gastos al reporte diario.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        report.gastos += amount
        report.updated_at = bogota_to_utc(now_bogota())
        return report
    
    @staticmethod
    def update_values(report: DailyReportDomain, reik: int = None, jackpot: int = None,
                     ganancias: int = None, gastos: int = None) -> DailyReportDomain:
        """
        Actualizar valores del reporte diario.
        """
        if reik is not None:
            if reik < 0:
                raise ValueError("El reik no puede ser negativo")
            report.reik = reik
        
        if jackpot is not None:
            if jackpot < 0:
                raise ValueError("El jackpot no puede ser negativo")
            report.jackpot = jackpot
        
        if ganancias is not None:
            if ganancias < 0:
                raise ValueError("Las ganancias no pueden ser negativas")
            report.ganancias = ganancias
        
        if gastos is not None:
            if gastos < 0:
                raise ValueError("Los gastos no pueden ser negativos")
            report.gastos = gastos
        
        report.updated_at = bogota_to_utc(now_bogota())
        return report

