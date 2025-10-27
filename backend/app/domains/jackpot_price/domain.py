"""
Dominio JackpotPrice - Lógica de negocio pura para premios de jackpot.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from app.shared.utils.timezone import now_bogota, bogota_to_utc


class JackpotPriceDomain(BaseModel):
    """
    Entidad de dominio JackpotPrice.
    Representa un premio de jackpot ganado en una sesión.
    """
    id: Optional[str] = None
    user_id: str
    session_id: str
    value: int
    winner_hand: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('value')
    def validate_value(cls, v):
        """Validar que el valor del jackpot sea positivo"""
        if v <= 0:
            raise ValueError('El valor del jackpot debe ser mayor a 0')
        return v
    
    def is_high_value(self, threshold: int = 10000) -> bool:
        """Verificar si es un jackpot de alto valor"""
        return self.value >= threshold
    
    def has_winner_hand(self) -> bool:
        """Verificar si tiene información de la mano ganadora"""
        return self.winner_hand is not None and len(self.winner_hand.strip()) > 0
    
    def validate_business_rules(self) -> list[str]:
        """
        Validar reglas de negocio del jackpot.
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
            errors.append("El valor del jackpot debe ser mayor a 0")
        
        return errors


class JackpotPriceDomainService:
    """
    Servicio de dominio para JackpotPrice.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_jackpot_price(user_id: str, session_id: str, value: int,
                            winner_hand: str = None, comment: str = None) -> JackpotPriceDomain:
        """
        Crear un nuevo premio de jackpot con validación de reglas de negocio.
        """
        jackpot_price = JackpotPriceDomain(
            user_id=user_id,
            session_id=session_id,
            value=value,
            winner_hand=winner_hand,
            comment=comment,
            created_at=bogota_to_utc(now_bogota()),
            updated_at=bogota_to_utc(now_bogota())
        )
        
        # Validar reglas de negocio
        errors = jackpot_price.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return jackpot_price
    
    @staticmethod
    def update_value(jackpot_price: JackpotPriceDomain, new_value: int) -> JackpotPriceDomain:
        """
        Actualizar el valor de un jackpot.
        """
        if new_value <= 0:
            raise ValueError("El valor del jackpot debe ser mayor a 0")
        
        jackpot_price.value = new_value
        jackpot_price.updated_at = bogota_to_utc(now_bogota())
        
        return jackpot_price
    
    @staticmethod
    def set_winner_hand(jackpot_price: JackpotPriceDomain, winner_hand: str) -> JackpotPriceDomain:
        """
        Establecer la mano ganadora del jackpot.
        """
        if not winner_hand or len(winner_hand.strip()) == 0:
            raise ValueError("La mano ganadora no puede estar vacía")
        
        jackpot_price.winner_hand = winner_hand.strip()
        jackpot_price.updated_at = bogota_to_utc(now_bogota())
        
        return jackpot_price
    
    @staticmethod
    def calculate_total_jackpots(jackpots: list[JackpotPriceDomain]) -> int:
        """
        Calcular el total de jackpots.
        """
        return sum(jackpot.value for jackpot in jackpots)
    
    @staticmethod
    def filter_high_value_jackpots(jackpots: list[JackpotPriceDomain], 
                                   threshold: int = 10000) -> list[JackpotPriceDomain]:
        """
        Filtrar jackpots de alto valor.
        """
        return [jackpot for jackpot in jackpots if jackpot.is_high_value(threshold)]
    
    @staticmethod
    def get_biggest_jackpot(jackpots: list[JackpotPriceDomain]) -> Optional[JackpotPriceDomain]:
        """
        Obtener el jackpot más grande.
        """
        if not jackpots:
            return None
        return max(jackpots, key=lambda x: x.value)

