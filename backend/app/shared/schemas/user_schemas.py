"""
Schemas Pydantic para la entidad User.
Estos schemas se usan para la validación de entrada/salida de la API.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.domains.user.domain import UserRole


class UserSecuritySchema(BaseModel):
    """Schema para información de seguridad del usuario"""
    failed_attempts: int = 0
    
    @field_validator('failed_attempts')
    def validate_failed_attempts(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Los intentos fallidos deben estar entre 0 y 5')
        return v


class UserCreateSchema(BaseModel):
    """Schema para crear un usuario"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    name: str
    roles: List[UserRole] = [UserRole.USER]
    
    @field_validator('password')
    def validate_password(cls, v):
        # Si no hay contraseña, es válido (se validará en la lógica de negocio)
        if v is None:
            return v
        
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v
    
    @field_validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        if len(v.strip()) > 100:
            raise ValueError('El nombre no puede exceder 100 caracteres')
        return v.strip()
    
    def validate_business_rules(self):
        """Validar reglas de negocio específicas según el rol"""
        errors = []
        
        # Si es DEALER, MANAGER o ADMIN, email y password son obligatorios
        privileged_roles = [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
        if any(role in privileged_roles for role in self.roles):
            if not self.email:
                errors.append('Los usuarios con rol Dealer, Manager o Admin deben tener email')
            if not self.password:
                errors.append('Los usuarios con rol Dealer, Manager o Admin deben tener contraseña')
        
        return errors


class UserUpdateSchema(BaseModel):
    """Schema para actualizar un usuario"""
    name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    is_active: Optional[bool] = None
    
    @field_validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('El nombre debe tener al menos 2 caracteres')
            if len(v.strip()) > 100:
                raise ValueError('El nombre no puede exceder 100 caracteres')
            return v.strip()
        return v


class UserResponseSchema(BaseModel):
    """Schema para respuesta de usuario (sin información sensible)"""
    id: str
    email: Optional[str] = None
    name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    security: UserSecuritySchema
    
    class Config:
        from_attributes = True


class UserLoginSchema(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class UserPasswordChangeSchema(BaseModel):
    """Schema para cambio de contraseña"""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('La nueva contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La nueva contraseña debe contener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La nueva contraseña debe contener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La nueva contraseña debe contener al menos un número')
        return v


class UserRoleUpdateSchema(BaseModel):
    """Schema para actualizar roles de usuario"""
    roles: List[UserRole]
    
    @field_validator('roles')
    def validate_roles(cls, v):
        if not v:
            raise ValueError('El usuario debe tener al menos un rol')
        if len(v) > 4:
            raise ValueError('Un usuario no puede tener más de 4 roles')
        return v


class UserListResponseSchema(BaseModel):
    """Schema para respuesta de lista de usuarios"""
    users: List[UserResponseSchema]
    total: int
    page: int
    limit: int


class UserStatsSchema(BaseModel):
    """Schema para estadísticas de usuarios"""
    total_users: int
    active_users: int
    inactive_users: int
    locked_users: int
    users_by_role: dict


# Schema para respuesta de autenticación
class TokenResponseSchema(BaseModel):
    """Schema para respuesta de token de autenticación"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponseSchema
