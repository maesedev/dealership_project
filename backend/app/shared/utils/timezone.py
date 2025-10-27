"""
Utilidades para manejo de zonas horarias.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def get_bogota_timezone() -> timezone:
    """
    Obtener la zona horaria de Bogotá (Colombia).
    Colombia usa UTC-5 (no tiene horario de verano).
    """
    return timezone(timedelta(hours=-5))


def now_bogota() -> datetime:
    """
    Obtener la fecha y hora actual en la zona horaria de Bogotá.
    """
    return datetime.now(get_bogota_timezone())


def utc_to_bogota(utc_datetime: datetime) -> datetime:
    """
    Convertir un datetime UTC a la zona horaria de Bogotá.
    """
    if utc_datetime.tzinfo is None:
        # Si no tiene timezone, asumir que es UTC
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    return utc_datetime.astimezone(get_bogota_timezone())


def bogota_to_utc(bogota_datetime: datetime) -> datetime:
    """
    Convertir un datetime de Bogotá a UTC.
    """
    if bogota_datetime.tzinfo is None:
        # Si no tiene timezone, asumir que es de Bogotá
        bogota_datetime = bogota_datetime.replace(tzinfo=get_bogota_timezone())
    
    return bogota_datetime.astimezone(timezone.utc)


def ensure_bogota_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Asegurar que un datetime tenga la zona horaria de Bogotá.
    Si es None, retorna None.
    Si no tiene timezone, asume que es de Bogotá.
    Si tiene timezone, lo convierte a Bogotá.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        return dt.replace(tzinfo=get_bogota_timezone())
    
    return dt.astimezone(get_bogota_timezone())
