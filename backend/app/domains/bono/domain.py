"""
Dominio Bono - Lógica de negocio pura para bonos.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from app.shared.utils.timezone import now_bogota, bogota_to_utc


class BonoDomain(BaseModel):
    """
    Entidad de dominio Bono.
    Representa un bono otorgado a un usuario en una sesión.
    """
    id: Optional[str] = None
    user_id: str
    session_id: str
    value: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('value')
    def validate_value(cls, v):
        """Validar que el valor del bono sea positivo"""
        if v <= 0:
            raise ValueError('El valor del bono debe ser mayor a 0')
        return v
    
    def is_significant(self, threshold: int = 1000) -> bool:
        """Verificar si el bono es significativo"""
        return self.value >= threshold
    
    def validate_business_rules(self) -> list[str]:
        """
        Validar reglas de negocio del bono.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar user_id
        if not self.user_id or len(self.user_id.strip()) == 0:
            errors.append("El user_id es obligatorio")
        
        # Validar session_id
        if not self.session_id or len(self.session_id.strip()) == 0:
            errors.append("El session_id es obligatorio")
        
        # Validar valor
        if self.value <= 0:
            errors.append("El valor del bono debe ser mayor a 0")
        
        return errors


class BonoDomainService:
    """
    Servicio de dominio para Bono.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_bono(user_id: str, session_id: str, value: int,
                   comment: str = None) -> BonoDomain:
        """
        Crear un nuevo bono con validación de reglas de negocio.
        """
        bono = BonoDomain(
            user_id=user_id,
            session_id=session_id,
            value=value,
            comment=comment,
            created_at=bogota_to_utc(now_bogota()),
            updated_at=bogota_to_utc(now_bogota())
        )
        
        # Validar reglas de negocio
        errors = bono.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return bono
    
    @staticmethod
    def update_value(bono: BonoDomain, new_value: int) -> BonoDomain:
        """
        Actualizar el valor de un bono.
        """
        if new_value <= 0:
            raise ValueError("El valor del bono debe ser mayor a 0")
        
        bono.value = new_value
        bono.updated_at = bogota_to_utc(now_bogota())
        
        return bono
    
    @staticmethod
    def calculate_total_bonos(bonos: list[BonoDomain]) -> int:
        """
        Calcular el total de bonos.
        """
        return sum(bono.value for bono in bonos)
    
    @staticmethod
    def filter_by_minimum_value(bonos: list[BonoDomain], min_value: int) -> list[BonoDomain]:
        """
        Filtrar bonos por valor mínimo.
        """
        return [bono for bono in bonos if bono.value >= min_value]

