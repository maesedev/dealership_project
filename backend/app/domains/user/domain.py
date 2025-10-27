"""
Dominio User - Lógica de negocio pura para usuarios.
"""

from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, validator
from enum import Enum
import re
from app.shared.utils import now_bogota


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
    
    Reglas:
    - Usuarios tipo USER: username y password opcionales, is_active = False por defecto
    - Usuarios Dealer/Manager/Admin: username y password obligatorios, is_active = True por defecto
    """
    id: Optional[str] = None
    username: Optional[str] = None
    hashed_password: str = ""  # Vacío para usuarios sin contraseña
    roles: List[UserRole] = [UserRole.USER]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: str
    security: SecurityInfo = SecurityInfo()
    
    def get_display_name(self) -> str:
        """Obtener nombre para mostrar"""
        if self.name:
            return self.name
        if self.username:
            return self.username
        return "Usuario sin nombre"
    
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
    
    def can_login(self) -> bool:
        """Verificar si el usuario puede iniciar sesión (debe tener username)"""
        return self.username is not None and len(self.username) > 0
    
    def validate_business_rules(self) -> List[str]:
        """
        Validar reglas de negocio del usuario.
        Retorna lista de errores encontrados.
        """
        errors = []
        
        # Validar username (opcional, pero si existe debe ser válido)
        if self.username and not self._is_valid_username_format(self.username):
            errors.append("El username no tiene un formato válido")
        
        # Validar nombre
        if not self.name or len(self.name.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        
        if len(self.name.strip()) > 100:
            errors.append("El nombre no puede exceder 100 caracteres")
        
        # Validar password hash (solo si no está vacío)
        # Usuarios tipo USER pueden no tener contraseña
        privileged_roles = [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
        is_privileged = any(role in privileged_roles for role in self.roles)
        
        if is_privileged and (not self.hashed_password or len(self.hashed_password) < 20):
            errors.append("Los usuarios Dealer/Manager/Admin deben tener una contraseña válida")
        
        # Validar roles
        if not self.roles:
            errors.append("El usuario debe tener al menos un rol")
        
        if len(self.roles) > 4:
            errors.append("Un usuario no puede tener más de 4 roles")
        
        # Validar información de seguridad
        if self.security.failed_attempts < 0 or self.security.failed_attempts > 5:
            errors.append("Los intentos fallidos deben estar entre 0 y 5")
        
        return errors
    
    def _is_valid_username_format(self, username: str) -> bool:
        """Validar formato de username"""
        # Username debe tener entre 3 y 50 caracteres
        # Solo letras, números, guiones bajos y guiones
        if len(username) < 3 or len(username) > 50:
            return False
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))


class UserDomainService:
    """
    Servicio de dominio para User.
    Contiene la lógica de negocio que opera sobre las entidades del dominio.
    """
    
    @staticmethod
    def create_user(username: Optional[str], hashed_password: str = "", name: str = "",
                   roles: List[UserRole] = None) -> UserDomain:
        """
        Crear un nuevo usuario con validación de reglas de negocio.
        
        Reglas:
        - Usuarios tipo USER: username y password opcionales, is_active = False por defecto
        - Usuarios Dealer/Manager/Admin: username y password obligatorios, is_active = True por defecto
        """
        if roles is None:
            roles = [UserRole.USER]
        
        user = UserDomain(
            username=username,
            hashed_password=hashed_password,
            name=name,
            roles=roles,
            created_at=now_bogota(),
            updated_at=now_bogota()
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
            user.updated_at = now_bogota()
        
        return user
    
    @staticmethod
    def remove_role(user: UserDomain, role: UserRole) -> UserDomain:
        """
        Remover un rol de un usuario.
        """
        if role in user.roles and len(user.roles) > 1:  # No permitir quitar todos los roles
            user.roles.remove(role)
            user.updated_at = datetime.now(timezone.utc)
        
        return user
    
    @staticmethod
    def activate_user(user: UserDomain) -> UserDomain:
        """
        Activar un usuario.
        """
        user.is_active = True
        user.security.failed_attempts = 0  # Resetear intentos fallidos
        user.updated_at = datetime.now(timezone.utc)
        return user
    
    @staticmethod
    def deactivate_user(user: UserDomain) -> UserDomain:
        """
        Desactivar un usuario.
        """
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
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
        
        user.updated_at = datetime.now(timezone.utc)
        return user
    
    @staticmethod
    def reset_failed_attempts(user: UserDomain) -> UserDomain:
        """
        Resetear intentos fallidos de login.
        """
        user.security.failed_attempts = 0
        user.updated_at = datetime.now(timezone.utc)
        return user
