"""
Dominio User - Lógica de negocio pura para usuarios.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from enum import Enum
import re


class UserRole(str, Enum):
    """Roles de usuario disponibles"""
    USER = "USER"
    ADMIN = "ADMIN"
    DEALER = "DEALER"
    MANAGER = "MANAGER"


class SecurityInfo(BaseModel):
    """Información de seguridad del usuario"""
    failed_attempts: int = 0
    
    @validator('failed_attempts')
    def validate_failed_attempts(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Los intentos fallidos deben estar entre 0 y 5')
        return v


class UserDomain(BaseModel):
    """
    Entidad de dominio User.
    Representa las reglas de negocio puras para un usuario.
    """
    id: Optional[str] = None
    email: EmailStr
    hashed_password: str
    roles: List[UserRole] = [UserRole.USER]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: str
    security: SecurityInfo = SecurityInfo()
    
    def get_display_name(self) -> str:
        """Obtener nombre para mostrar"""
        return self.name or self.email.split('@')[0]
    
    def has_role(self, role: UserRole) -> bool:
        """Verificar si el usuario tiene un rol específico"""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Verificar si el usuario es administrador"""
        return UserRole.ADMIN in self.roles
    
    def is_dealer(self) -> bool:
        """Verificar si el usuario es vendedor"""
        return UserRole.DEALER in self.roles
    
    def is_manager(self) -> bool:
        """Verificar si el usuario es gerente"""
        return UserRole.MANAGER in self.roles
    
    def can_access_admin_features(self) -> bool:
        """Verificar si puede acceder a funciones de administración"""
        return self.is_admin() or self.is_dealer()
    
    def is_locked(self) -> bool:
        """Verificar si la cuenta está bloqueada por intentos fallidos"""
        return self.security.failed_attempts >= 5
    
    def validate_business_rules(self) -> List[str]:
        """
        Validar reglas de negocio del usuario.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar email
        if not self.email or not self._is_valid_email_format(self.email):
            errors.append("El email no tiene un formato válido")
        
        # Validar nombre
        if not self.name or len(self.name.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        
        if len(self.name.strip()) > 100:
            errors.append("El nombre no puede exceder 100 caracteres")
        
        # Validar password hash
        if not self.hashed_password or len(self.hashed_password) < 20:
            errors.append("El hash de la contraseña no es válido")
        
        # Validar roles
        if not self.roles:
            errors.append("El usuario debe tener al menos un rol")
        
        if len(self.roles) > 4:
            errors.append("Un usuario no puede tener más de 4 roles")
        
        # Validar información de seguridad
        if self.security.failed_attempts < 0 or self.security.failed_attempts > 5:
            errors.append("Los intentos fallidos deben estar entre 0 y 5")
        
        return errors
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class UserDomainService:
    """
    Servicio de dominio para User.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_user(email: str, hashed_password: str, name: str,
                   roles: List[UserRole] = None) -> UserDomain:
        """
        Crear un nuevo usuario con validación de reglas de negocio.
        """
        if roles is None:
            roles = [UserRole.USER]
        
        user = UserDomain(
            email=email,
            hashed_password=hashed_password,
            name=name,
            roles=roles,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Validar reglas de negocio
        errors = user.validate_business_rules()
        if errors:
            raise ValueError(f"Errores de validación: {'; '.join(errors)}")
        
        return user
    
    @staticmethod
    def add_role(user: UserDomain, role: UserRole) -> UserDomain:
        """
        Agregar un rol a un usuario.
        """
        if role not in user.roles:
            user.roles.append(role)
            user.updated_at = datetime.utcnow()
        
        return user
    
    @staticmethod
    def remove_role(user: UserDomain, role: UserRole) -> UserDomain:
        """
        Remover un rol de un usuario.
        """
        if role in user.roles and len(user.roles) > 1:  # No permitir quitar todos los roles
            user.roles.remove(role)
            user.updated_at = datetime.utcnow()
        
        return user
    
    @staticmethod
    def activate_user(user: UserDomain) -> UserDomain:
        """
        Activar un usuario.
        """
        user.is_active = True
        user.security.failed_attempts = 0  # Resetear intentos fallidos
        user.updated_at = datetime.utcnow()
        return user
    
    @staticmethod
    def deactivate_user(user: UserDomain) -> UserDomain:
        """
        Desactivar un usuario.
        """
        user.is_active = False
        user.updated_at = datetime.utcnow()
        return user
    
    @staticmethod
    def record_failed_attempt(user: UserDomain) -> UserDomain:
        """
        Registrar un intento fallido de login.
        """
        user.security.failed_attempts += 1
        
        # Bloquear cuenta después de 5 intentos fallidos
        if user.security.failed_attempts >= 5:
            user.is_active = False
        
        user.updated_at = datetime.utcnow()
        return user
    
    @staticmethod
    def reset_failed_attempts(user: UserDomain) -> UserDomain:
        """
        Resetear intentos fallidos de login.
        """
        user.security.failed_attempts = 0
        user.updated_at = datetime.utcnow()
        return user
