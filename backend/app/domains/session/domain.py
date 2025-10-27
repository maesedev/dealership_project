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
        Convierte cualquier datetime a hora de Bogotá y luego a UTC.
        
        Proceso:
        1. Si el datetime es naive (sin timezone), se asume que ya está en hora de Bogotá
        2. Si tiene timezone, se convierte a hora de Bogotá
        3. Se retorna en UTC para almacenamiento consistente
        
        Ejemplo:
        - Input: 2025-10-26 14:00:00 (China, UTC+8)
        - Hora de Bogotá: 2025-10-26 01:00:00-05:00
        - Output UTC: 2025-10-26 06:00:00+00:00
        """
        if dt is None:
            return None
            
        # Si es naive, asumirlo como hora de Bogotá
        if dt.tzinfo is None:
            dt_bogota = dt.replace(tzinfo=BOGOTA_TZ)
        else:
            # Convertir a hora de Bogotá
            dt_bogota = dt.astimezone(BOGOTA_TZ)
        
        # Convertir a UTC para almacenamiento
        return dt_bogota.astimezone(timezone.utc)
    
    @field_validator('start_time', 'end_time', 'created_at', 'updated_at', mode='before')
    def normalize_to_bogota_utc(cls, v):
        """
        Normalizar todos los datetimes a hora de Bogotá en formato UTC.
        Esto asegura que sin importar desde dónde se envíe el timestamp,
        siempre se almacene el momento correcto en hora de Bogotá.
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
        
        return cls.convert_to_bogota_utc(v)
    
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
        El end_time se convierte automáticamente a hora de Bogotá.
        
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
            # Obtener hora actual de Bogotá y convertir a UTC
            end_time = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
        # El validator se encargará de convertir end_time a hora de Bogotá
        if end_time < session.start_time:
            raise ValueError("El tiempo de fin no puede ser anterior al tiempo de inicio")
        
        session.end_time = end_time
        session.updated_at = datetime.now(BOGOTA_TZ).astimezone(timezone.utc)
        
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
