"""
Dominio Session - Lógica de negocio pura para sesiones de dealer.
Todas las fechas se convierten automáticamente a hora de Bogotá en formato UTC ISO.
"""

from typing import Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pydantic import BaseModel, field_validator


# Zona horaria de Bogotá
BOGOTA_TZ = ZoneInfo("America/Bogota")


class SessionDomain(BaseModel):
    """
    Entidad de dominio Session.
    Representa una sesión de trabajo de un dealer.
    Todas las fechas se almacenan en UTC pero representan momentos en hora de Bogotá.
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
    
    @staticmethod
    def convert_to_bogota_utc(dt: datetime) -> datetime:
        """
        Convierte cualquier datetime representando el momento actual a UTC.
        
        Proceso simplificado:
        1. Si el datetime es naive (sin timezone), se asume que representa la hora actual de Bogotá
        2. Si tiene timezone UTC, representa el momento actual y se usa directamente
        3. Si tiene otra timezone, se convierte a Bogotá primero
        """
        if dt is None:
            return None
            
        # Si es naive, asumirlo como hora de Bogotá y convertir a UTC
        if dt.tzinfo is None:
            dt_bogota = dt.replace(tzinfo=BOGOTA_TZ)
            return dt_bogota.astimezone(timezone.utc)
        
        # Si es UTC, usar directamente (representa el momento actual)
        if dt.tzinfo == timezone.utc:
            return dt
        
        # Si tiene otra timezone, convertir a Bogotá y luego a UTC
        dt_bogota = dt.astimezone(BOGOTA_TZ)
        return dt_bogota.astimezone(timezone.utc)
    
    @field_validator('start_time', 'end_time', 'created_at', 'updated_at', mode='before')
    def normalize_to_utc(cls, v):
        """
        Normalizar todos los datetimes a UTC para almacenamiento consistente.
        Evitar conversiones complejas que causen problemas de comparación.
        """
        if v is None:
            return v
        
        # Si viene como string, parsearlo primero
        if isinstance(v, str):
            try:
                v = datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Intentar otros formatos comunes
                v = datetime.fromisoformat(v)
        
        # Si no es datetime, retornar tal como está
        if not isinstance(v, datetime):
            return v
        
        # Si ya tiene timezone UTC, usar directamente
        if v.tzinfo == timezone.utc:
            return v
        
        # Si no tiene timezone, asumir que es UTC (simplificado)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        
        # Si tiene otra timezone, convertir a UTC
        return v.astimezone(timezone.utc)
    
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
    
    def get_bogota_time(self, dt: datetime) -> datetime:
        """Obtener un datetime en hora de Bogotá para visualización"""
        if dt is None:
            return None
        return dt.astimezone(BOGOTA_TZ)
    
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
        El start_time se convierte automáticamente a hora de Bogotá.
        """
        if start_time is None:
            # Obtener hora actual de Bogotá y convertir a UTC
            start_time = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        now_bogota_utc = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        session = SessionDomain(
            dealer_id=dealer_id,
            start_time=start_time,
            hourly_pay=hourly_pay,
            comment=comment,
            created_at=now_bogota_utc,
            updated_at=now_bogota_utc
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
        - El tiempo de fin no puede ser anterior al de inicio
        """
        # Validar que la sesión no haya sido terminada previamente
        if session.end_time is not None:
            raise ValueError("Esta sesión ya fue terminada anteriormente")
        
        if end_time is None:
            # Obtener hora actual como UTC directo
            end_time = datetime.now(timezone.utc)
        
        # Asegurar que ambos timestamps sean comparables (ambos UTC)
        start_time_utc = session.start_time
        if start_time_utc.tzinfo is None:
            start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)
        elif start_time_utc.tzinfo != timezone.utc:
            start_time_utc = start_time_utc.astimezone(timezone.utc)
            
        end_time_utc = end_time
        if end_time_utc.tzinfo is None:
            end_time_utc = end_time_utc.replace(tzinfo=timezone.utc)
        elif end_time_utc.tzinfo != timezone.utc:
            end_time_utc = end_time_utc.astimezone(timezone.utc)
        
        # Comparar en UTC
        if end_time_utc < start_time_utc:
            raise ValueError("El tiempo de fin no puede ser anterior al tiempo de inicio")
        
        session.end_time = end_time_utc
        session.updated_at = datetime.now(timezone.utc)
        
        return session
    
    @staticmethod
    def add_jackpot(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar monto al jackpot de la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.jackpot += amount
        session.updated_at = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        return session
    
    @staticmethod
    def add_reik(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar monto al reik de la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.reik += amount
        session.updated_at = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        return session
    
    @staticmethod
    def add_tips(session: SessionDomain, amount: int) -> SessionDomain:
        """
        Agregar propinas a la sesión.
        """
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
        
        session.tips += amount
        session.updated_at = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        return session
