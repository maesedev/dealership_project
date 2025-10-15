"""
Servicio User - Orquestador de lógica de usuarios.
Este servicio consume el dominio User pero no lo modifica.
Se encarga de la comunicación con la base de datos y orquestación de operaciones.
"""

from typing import List, Optional
from datetime import datetime
import bcrypt
from app.domains.user.domain import UserDomain, UserDomainService, UserRole
from app.infrastructure.database.connection import get_database


class UserService:
    """
    Servicio de aplicación para User.
    Consume el dominio User y maneja la persistencia.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.users
        self.domain_service = UserDomainService()
    
    def _hash_password(self, password: str) -> str:
        """Hashear una contraseña usando bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verificar una contraseña contra su hash"""
        # Si el hash está vacío, el usuario no tiene contraseña
        if not hashed_password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def create_user(self, email: Optional[str], password: Optional[str], name: str,
                         roles: List[UserRole] = None) -> UserDomain:
        """
        Crear un nuevo usuario usando el dominio.
        
        Reglas de negocio:
        - Usuarios tipo USER: email y password opcionales, is_active = False por defecto
        - Usuarios Dealer/Manager/Admin: email y password obligatorios, is_active = True por defecto
        """
        if roles is None:
            roles = [UserRole.USER]
        
        # Validar reglas de negocio según el rol
        privileged_roles = [UserRole.DEALER, UserRole.MANAGER, UserRole.ADMIN]
        is_privileged = any(role in privileged_roles for role in roles)
        
        if is_privileged:
            # Dealers, Managers y Admins DEBEN tener email y password
            if not email:
                raise ValueError("Los usuarios con rol Dealer, Manager o Admin deben tener email")
            if not password:
                raise ValueError("Los usuarios con rol Dealer, Manager o Admin deben tener contraseña")
        
        # Verificar que el email no exista si se proporcionó
        if email:
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                raise ValueError("El email ya está registrado")
        
        # Hashear la contraseña (si se proporcionó)
        if password:
            hashed_password = self._hash_password(password)
        else:
            # Para usuarios sin contraseña, usar un hash vacío o un valor por defecto
            hashed_password = ""
        
        # Determinar el estado inicial según el rol
        # Usuarios tipo USER: is_active = False (deben ser activados por un admin)
        # Dealers/Managers/Admins: is_active = True (pueden iniciar sesión inmediatamente)
        is_active = is_privileged
        
        # Usar el servicio de dominio para crear el usuario
        user = self.domain_service.create_user(
            email=email,
            hashed_password=hashed_password,
            name=name,
            roles=roles
        )
        
        # Establecer el estado activo según el rol
        user.is_active = is_active
        
        # Convertir a diccionario para MongoDB
        user_dict = user.dict(exclude={"id"})
        user_dict["created_at"] = user.created_at
        user_dict["updated_at"] = user.updated_at
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(user_dict)
        
        # Actualizar el ID generado
        user.id = str(result.inserted_id)
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserDomain]:
        """
        Obtener un usuario por ID.
        """
        user_data = await self.collection.find_one({"_id": user_id})
        
        if user_data:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
            return UserDomain(**user_data)
        
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserDomain]:
        """
        Obtener un usuario por email.
        """
        user_data = await self.collection.find_one({"email": email})
        
        if user_data:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
            return UserDomain(**user_data)
        
        return None
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserDomain]:
        """
        Obtener todos los usuarios con paginación.
        """
        cursor = self.collection.find().skip(skip).limit(limit)
        users = []
        
        async for user_data in cursor:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
            users.append(UserDomain(**user_data))
        
        return users
    
    async def get_users_by_role(self, role: UserRole) -> List[UserDomain]:
        """
        Obtener usuarios por rol específico.
        """
        cursor = self.collection.find({"roles": role.value})
        users = []
        
        async for user_data in cursor:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
            users.append(UserDomain(**user_data))
        
        return users
    
    async def update_user(self, user_id: str, **updates) -> Optional[UserDomain]:
        """
        Actualizar un usuario existente.
        """
        # Obtener el usuario actual
        existing_user = await self.get_user_by_id(user_id)
        
        if not existing_user:
            return None
        
        # Usar el servicio de dominio para actualizar
        updated_user = self.domain_service.update_customer(existing_user, **updates)
        
        # Convertir a diccionario para actualización
        update_data = updated_user.dict(exclude={"id", "created_at", "hashed_password"})
        
        # Actualizar en la base de datos
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        return updated_user
    
    async def update_user_roles(self, user_id: str, roles: List[UserRole]) -> Optional[UserDomain]:
        """
        Actualizar roles de un usuario.
        """
        existing_user = await self.get_user_by_id(user_id)
        
        if not existing_user:
            return None
        
        existing_user.roles = roles
        existing_user.updated_at = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"roles": [role.value for role in roles], "updated_at": existing_user.updated_at}}
        )
        
        return existing_user
    
    async def activate_user(self, user_id: str) -> Optional[UserDomain]:
        """
        Activar un usuario.
        """
        existing_user = await self.get_user_by_id(user_id)
        
        if not existing_user:
            return None
        
        activated_user = self.domain_service.activate_user(existing_user)
        
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {
                "is_active": True,
                "security.failed_attempts": 0,
                "updated_at": activated_user.updated_at
            }}
        )
        
        return activated_user
    
    async def deactivate_user(self, user_id: str) -> Optional[UserDomain]:
        """
        Desactivar un usuario.
        """
        existing_user = await self.get_user_by_id(user_id)
        
        if not existing_user:
            return None
        
        deactivated_user = self.domain_service.deactivate_user(existing_user)
        
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {
                "is_active": False,
                "updated_at": deactivated_user.updated_at
            }}
        )
        
        return deactivated_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserDomain]:
        """
        Autenticar un usuario con email y contraseña.
        Solo usuarios con email pueden iniciar sesión.
        """
        user = await self.get_user_by_email(email)
        
        if not user:
            return None
        
        # Verificar que el usuario pueda iniciar sesión (debe tener email)
        if not user.can_login():
            return None
        
        if not user.is_active:
            return None
        
        if user.is_locked():
            return None
        
        if not self._verify_password(password, user.hashed_password):
            # Registrar intento fallido
            user = self.domain_service.record_failed_attempt(user)
            await self.collection.update_one(
                {"_id": user.id},
                {"$set": {
                    "security.failed_attempts": user.security.failed_attempts,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at
                }}
            )
            return None
        
        # Resetear intentos fallidos en login exitoso
        if user.security.failed_attempts > 0:
            user = self.domain_service.reset_failed_attempts(user)
            await self.collection.update_one(
                {"_id": user.id},
                {"$set": {
                    "security.failed_attempts": 0,
                    "updated_at": user.updated_at
                }}
            )
        
        return user
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Cambiar la contraseña de un usuario.
        """
        user = await self.get_user_by_id(user_id)
        
        if not user:
            return False
        
        if not self._verify_password(current_password, user.hashed_password):
            return False
        
        new_hashed_password = self._hash_password(new_password)
        
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {
                "hashed_password": new_hashed_password,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Eliminar un usuario.
        """
        result = await self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    
    async def search_users(self, search_term: str) -> List[UserDomain]:
        """
        Buscar usuarios por nombre o email.
        """
        # Crear índice de texto si no existe
        await self.collection.create_index([
            ("name", "text"),
            ("email", "text")
        ])
        
        cursor = self.collection.find({"$text": {"$search": search_term}})
        users = []
        
        async for user_data in cursor:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
            users.append(UserDomain(**user_data))
        
        return users
    
    async def get_user_stats(self) -> dict:
        """
        Obtener estadísticas de usuarios.
        """
        total_users = await self.collection.count_documents({})
        active_users = await self.collection.count_documents({"is_active": True})
        inactive_users = await self.collection.count_documents({"is_active": False})
        locked_users = await self.collection.count_documents({"security.failed_attempts": {"$gte": 5}})
        
        # Estadísticas por rol
        users_by_role = {}
        for role in UserRole:
            count = await self.collection.count_documents({"roles": role.value})
            users_by_role[role.value] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "locked_users": locked_users,
            "users_by_role": users_by_role
        }
