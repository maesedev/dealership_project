"""
Dominio Session - Lógica de negocio pura para sesiones de dealer.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from app.shared.utils import now_bogota, get_bogota_timezone, ensure_bogota_timezone


class SessionDomain(BaseModel):
    """
    Entidad de dominio Session.
    Representa una sesión de trabajo de un dealer.
    """
    id: Optional[str] = None
    dealer_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    jackpot: int = 0
    reik: int = 0
    tips: int = 0
    hourly_pay: int = 0
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('start_time', 'end_time', 'created_at', 'updated_at')
    def ensure_timezone_aware(cls, v):
        """Asegurar que todos los datetimes tengan información de zona horaria (Bogotá)"""
        if v is None:
            return v
        # Si el datetime es naive (sin timezone), asumirlo como Bogotá
        if v.tzinfo is None:
            return v.replace(tzinfo=get_bogota_timezone())
        # Convertir a zona horaria de Bogotá
        return ensure_bogota_timezone(v)
    
    @field_validator('jackpot', 'reik', 'tips', 'hourly_pay')
    def validate_positive_values(cls, v):
        """Validar que los valores monetarios no sean negativos"""
        if v < 0:
            raise ValueError('Los valores monetarios no pueden ser negativos')
        return v
    
    def is_active(self) -> bool:
        """Verificar si la sesión está activa"""
        return self.end_time is None
    
    def get_duration(self) -> Optional[float]:
        """Obtener duración de la sesión en horas"""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    def get_total_earnings(self) -> int:
        """Calcular ganancias totales de la sesión"""
        return self.jackpot + self.reik + self.tips + self.hourly_pay
    
    def validate_business_rules(self) -> list[str]:
        """
        Validar reglas de negocio de la sesión.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar dealer_id
        if not self.dealer_id or len(self.dealer_id.strip()) == 0:
            errors.append("El dealer_id es obligatorio")
        
        # Validar tiempos
        if self.end_time and self.end_time < self.start_time:
            errors.append("El tiempo de fin no puede ser anterior al tiempo de inicio")
        
        # Validar valores monetarios
        if self.jackpot < 0:
            errors.append("El jackpot no puede ser negativo")
        if self.reik < 0:
            errors.append("El reik no puede ser negativo")
        if self.tips < 0:
            errors.append("Las propinas no pueden ser negativas")
        if self.hourly_pay < 0:
            errors.append("El pago por hora no puede ser negativo")
        
        return errors


class SessionDomainService:
    """
    Servicio de dominio para Session.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_session(dealer_id: str, start_time: datetime = None,
                      hourly_pay: int = 0, comment: str = None) -> SessionDomain:
        """
        Crear una nueva sesión con validación de reglas de negocio.
        """
        start_time = now_bogota().isoformat().replace('-05:00', 'Z')
            

        session = SessionDomain(
            dealer_id=dealer_id,
            start_time=start_time,
            hourly_pay=hourly_pay,
            comment=comment,
            created_at=start_time,
            updated_at=start_time
        )
        
        # Validar reglas de negocio
        errors = session.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return session
    
    @staticmethod
    def end_session(session: SessionDomain, end_time: datetime = None) -> SessionDomain:
        """
        Finalizar una sesión.
        
        Validación:
        - No permite terminar una sesión que ya fue terminada
        - El jackpot debe ser mayor a cero
        - El reik debe ser mayor a cero
        """
        # Validar que la sesión no haya sido terminada previamente
        if session.end_time is not None:
            raise ValueError("Esta sesión ya fue terminada anteriormente")
        
        # Validar que el jackpot sea mayor a cero
        if session.jackpot <= 0:
            raise ValueError("El jackpot debe ser mayor a cero para terminar la sesión")
        
        # Validar que el reik sea mayor a cero
        if session.reik <= 0:
            raise ValueError("El reik debe ser mayor a cero para terminar la sesión")
        
        if end_time is None:
            end_time = now_bogota()
        
        if end_time < session.start_time:
            raise ValueError("El tiempo de fin no puede ser anterior al tiempo de inicio")
        
        session.end_time = end_time
        session.updated_at = now_bogota()
        
        return session
    
    @staticmethod
    def add_jackpot(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar monto al jackpot de la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.jackpot += amount
        session.updated_at = now_bogota()
        
        return session
    
    @staticmethod
    def add_reik(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar monto al reik de la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.reik += amount
        session.updated_at = now_bogota()
        
        return session
    
    @staticmethod
    def add_tips(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar propinas a la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.tips += amount
        session.updated_at = now_bogota()
        
        return session
