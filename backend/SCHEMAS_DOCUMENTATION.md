# Documentación de Schemas de Usuario

## 📋 Estructura del Documento User en MongoDB

### Documento Principal
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "email": "user@example.com",
  "hashed_password": "$2b$12$e7hTt2xQ8q9wE3rT5yU6iO9pA2sD4fG7hJ8kL1mN3oP6qR9tU2vW5xY8zA1bC4eF",
  "roles": ["user", "admin", "dealer", "consultant"],
  "is_active": true,
  "created_at": ISODate("2025-01-06T21:00:00Z"),
  "updated_at": ISODate("2025-01-06T21:00:00Z"),
  "name": "John Doe",
  "security": {
    "failed_attempts": 0
  }
}
```

## 🏗️ Arquitectura Implementada

### 1. **Dominio User** (`app/domains/user/`)
- **`UserDomain`**: Entidad con lógica de negocio pura
- **`UserDomainService`**: Servicios de dominio sin dependencias externas
- **`UserRole`**: Enum con roles disponibles (user, admin, dealer, consultant)
- **`SecurityInfo`**: Información de seguridad del usuario

### 2. **Schemas Pydantic** (`app/shared/schemas/user_schemas.py`)
- **`UserCreateSchema`**: Validación para crear usuarios
- **`UserUpdateSchema`**: Validación para actualizar usuarios
- **`UserResponseSchema`**: Respuesta sin información sensible
- **`UserLoginSchema`**: Validación para login
- **`UserPasswordChangeSchema`**: Validación para cambio de contraseña
- **`UserRoleUpdateSchema`**: Validación para actualizar roles
- **`UserListResponseSchema`**: Respuesta de lista paginada
- **`UserStatsSchema`**: Estadísticas de usuarios
- **`TokenResponseSchema`**: Respuesta de autenticación

### 3. **Servicio UserService** (`app/services/user_service/`)
- **`UserService`**: Orquestador que consume el dominio
- Maneja persistencia en MongoDB
- Implementa autenticación con bcrypt
- Gestiona seguridad y bloqueo de cuentas

## 🔐 Características de Seguridad

### Contraseñas
- **Hashing**: bcrypt con salt automático
- **Validación**: Mínimo 8 caracteres, mayúscula, minúscula, número
- **Verificación**: Método seguro de comparación

### Seguridad de Cuenta
- **Intentos fallidos**: Máximo 5 intentos (0-5)
- **Bloqueo automático**: Cuenta desactivada después de 5 intentos
- **Reset de intentos**: Al login exitoso o activación manual

### Roles y Permisos
- **user**: Usuario básico
- **admin**: Administrador del sistema
- **dealer**: Vendedor/concesionario
- **consultant**: Consultor de vehículos

## 📊 Endpoints Disponibles

### Gestión de Usuarios
- `POST /api/v1/users/` - Crear usuario
- `GET /api/v1/users/{user_id}` - Obtener usuario por ID
- `GET /api/v1/users/` - Lista paginada de usuarios
- `PUT /api/v1/users/{user_id}` - Actualizar usuario
- `DELETE /api/v1/users/{user_id}` - Eliminar usuario

### Gestión de Roles
- `PUT /api/v1/users/{user_id}/roles` - Actualizar roles

### Gestión de Estado
- `POST /api/v1/users/{user_id}/activate` - Activar usuario
- `POST /api/v1/users/{user_id}/deactivate` - Desactivar usuario

### Estadísticas
- `GET /api/v1/users/stats/overview` - Estadísticas de usuarios

## 🔧 Validaciones de Negocio

### Creación de Usuario
- Email único y válido
- Contraseña segura (8+ caracteres, mayúscula, minúscula, número)
- Nombre entre 2-100 caracteres
- Al menos un rol asignado
- Máximo 4 roles por usuario

### Seguridad
- Intentos fallidos entre 0-5
- Bloqueo automático en 5 intentos
- Reset de intentos en login exitoso
- Validación de formato de email con regex

## 📝 Ejemplos de Uso

### Crear Usuario
```python
user_data = UserCreateSchema(
    email="nuevo@example.com",
    password="MiPassword123",
    name="Juan Pérez",
    roles=[UserRole.USER, UserRole.DEALER]
)
```

### Autenticar Usuario
```python
user = await user_service.authenticate_user(
    email="user@example.com",
    password="MiPassword123"
)
```

### Actualizar Roles
```python
await user_service.update_user_roles(
    user_id="507f1f77bcf86cd799439011",
    roles=[UserRole.ADMIN, UserRole.DEALER]
)
```

## 🗄️ Índices de MongoDB Recomendados

```javascript
// Índice único en email
db.users.createIndex({ "email": 1 }, { unique: true })

// Índice de texto para búsqueda
db.users.createIndex({ "name": "text", "email": "text" })

// Índice en roles para consultas rápidas
db.users.createIndex({ "roles": 1 })

// Índice en estado activo
db.users.createIndex({ "is_active": 1 })
```

## 🚀 Próximos Pasos

1. **Autenticación JWT**: Implementar tokens de acceso
2. **Middleware de Autorización**: Verificar roles en endpoints
3. **Auditoría**: Log de acciones de usuarios
4. **Rate Limiting**: Limitar intentos de login por IP
5. **Notificaciones**: Alertas por bloqueo de cuenta
