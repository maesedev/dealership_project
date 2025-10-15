# Dealership Backend API

API backend para sistema de concesionario de vehículos construida con FastAPI y MongoDB.

## Arquitectura

Esta aplicación sigue una arquitectura orientada a dominios y servicios:

### Estructura de Carpetas

```
backend/
├── app/
│   ├── core/                    # Configuración y utilidades centrales
│   │   ├── config.py           # Configuración de la aplicación
│   │   └── __init__.py
│   ├── domains/                 # Dominios - Lógica de negocio pura
│   │   ├── customer/           # Dominio Customer
│   │   │   ├── domain.py       # Entidades y reglas de negocio
│   │   │   └── __init__.py
│   │   ├── vehicle/            # Dominio Vehicle
│   │   │   ├── domain.py       # Entidades y reglas de negocio
│   │   │   └── __init__.py
│   │   ├── sale/               # Dominio Sale
│   │   │   ├── domain.py       # Entidades y reglas de negocio
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── services/               # Servicios - Consumidores de dominios
│   │   ├── customer_service/   # Servicio Customer
│   │   │   ├── service.py      # Orquestador de lógica
│   │   │   └── __init__.py
│   │   ├── vehicle_service/    # Servicio Vehicle
│   │   │   ├── service.py      # Orquestador de lógica
│   │   │   └── __init__.py
│   │   ├── sale_service/       # Servicio Sale
│   │   │   ├── service.py      # Orquestador de lógica
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── api/                    # API - Endpoints y rutas
│   │   └── v1/                 # Versión 1 de la API
│   │       ├── router.py       # Router principal
│   │       └── __init__.py
│   ├── infrastructure/         # Infraestructura - Base de datos y config
│   │   ├── database/           # Configuración de base de datos
│   │   │   ├── connection.py   # Conexión a MongoDB
│   │   │   └── __init__.py
│   │   └── __init__.py
│   └── shared/                 # Elementos compartidos
│       ├── models/             # Modelos compartidos
│       ├── schemas/            # Esquemas Pydantic
│       ├── utils/              # Utilidades compartidas
│       └── __init__.py
├── main.py                     # Aplicación principal FastAPI
├── requirements.txt            # Dependencias Python
├── env.example                 # Ejemplo de variables de entorno
└── README.md                   # Este archivo
```

## Principios de Arquitectura

### Dominios (Domains)
- **Propósito**: Contienen la lógica de negocio pura
- **Características**: 
  - NO tienen dependencias externas (como base de datos)
  - Contienen entidades, reglas de negocio y validaciones
  - Son independientes de frameworks y tecnologías

### Servicios (Services)
- **Propósito**: Consumen los dominios pero no los modifican
- **Características**:
  - Orquestan operaciones complejas
  - Manejan la comunicación con la base de datos
  - Coordinan entre múltiples dominios
  - NO modifican la lógica de negocio de los dominios

## Instalación y Configuración

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Ejecutar MongoDB**:
   ```bash
   # Asegúrate de que MongoDB esté ejecutándose
   mongod
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python main.py
   # O usando uvicorn directamente:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Uso

Una vez ejecutándose, puedes acceder a:

- **API Principal**: http://localhost:8000/
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 🔐 Sistema de Autenticación

El proyecto incluye un sistema completo de autenticación con JWT. 

**Inicio Rápido:**
```bash
# Ejecutar script de prueba
python examples/test_auth.py

# O seguir la guía rápida
# Ver: QUICK_START_AUTH.md
```

**Documentación:**
- 📚 **Guía completa**: `AUTH_DOCUMENTATION.md`
- 🚀 **Inicio rápido**: `QUICK_START_AUTH.md`
- 📖 **README del servicio**: `app/services/auth_service/README.md`
- 🧪 **Ejemplos**: Carpeta `examples/`

**Características:**
- ✅ Login con username y contraseña
- ✅ JWT (JSON Web Tokens)
- ✅ Verificación de tokens
- ✅ Refresh de tokens
- ✅ Control de roles (ADMIN, DEALER, MANAGER, USER)
- ✅ Intentos fallidos y bloqueo de cuenta
- ✅ Dependencias para proteger endpoints

## Endpoints Disponibles

### General
- `GET /` - Hello World
- `GET /api/v1/health` - Health check
- `GET /docs` - Documentación interactiva

### Autenticación 🔐
- `POST /api/v1/auth/login` - Login con username y contraseña
- `POST /api/v1/auth/refresh` - Refrescar token JWT
- `GET /api/v1/auth/me` - Obtener usuario autenticado

### Usuarios
- Ver `USER_SCHEMA_DOCUMENTATION.md` para endpoints de usuarios

## Desarrollo

### Agregar un Nuevo Dominio

1. Crear carpeta en `app/domains/nuevo_dominio/`
2. Implementar `domain.py` con entidades y reglas de negocio
3. Crear servicio correspondiente en `app/services/nuevo_dominio_service/`
4. Agregar rutas en `app/api/v1/`

### Agregar un Nuevo Servicio

1. Crear carpeta en `app/services/nuevo_servicio/`
2. Implementar `service.py` que consuma los dominios necesarios
3. NO modificar la lógica de negocio de los dominios

### Proteger Endpoints con **Autenticación**

```python
from fastapi import APIRouter, Depends
from app.shared.dependencies.auth import (
    get_current_active_user,
    require_admin,
    RoleChecker
)
from app.domains.user.domain import UserDomain

router = APIRouter()

# Endpoint protegido - requiere autenticación
@router.get("/protected")
async def protected_endpoint(user: UserDomain = Depends(get_current_active_user)):
    return {"message": f"Hola {user.name}"}

# Endpoint solo para admins
@router.delete("/admin-only", dependencies=[Depends(require_admin)])
async def admin_endpoint():
    return {"message": "Solo admins"}
```

Ver más ejemplos en `examples/protected_endpoint_example.py`

## 📚 Documentación Adicional

- **Sistema de Usuarios**: `USER_SCHEMA_DOCUMENTATION.md`
- **Sistema de Autenticación**: `AUTH_DOCUMENTATION.md`
- **Inicio Rápido Auth**: `QUICK_START_AUTH.md`
- **Ejemplos de Código**: Carpeta `examples/`

## 🧪 Scripts de Prueba

```bash
# Probar sistema de autenticación
python examples/test_auth.py

# Ver pruebas HTTP
# Abrir: examples/http_requests_auth.http
```

## 🔒 Seguridad

- Las contraseñas se hashean con **bcrypt**
- Los tokens son **JWT firmados con HS256**
- Tokens expiran en **30 minutos** (configurable)
- **5 intentos fallidos** antes de bloquear cuenta
- Solo usuarios **activos** pueden autenticarse

⚠️ **IMPORTANTE**: En producción, cambiar `SECRET_KEY` en el archivo `.env`

---

## 📋 API Reference - Endpoints y Schemas

### 🔑 Autenticación (`/api/v1/auth`)

#### `POST /api/v1/auth/login`
**Descripción**: Login con username y contraseña  
**Permisos**: Público  
**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```
**Response**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "string",
    "username": "string",
    "name": "string",
    "roles": ["USER", "DEALER", "MANAGER", "ADMIN"],
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "security": {
      "failed_attempts": 0
    }
  }
}
```

#### `POST /api/v1/auth/refresh`
**Descripción**: Refrescar token JWT  
**Permisos**: Usuario autenticado  
**Headers**: `Authorization: Bearer {token}`  
**Response**: Mismo schema que login

#### `GET /api/v1/auth/me`
**Descripción**: Obtener información del usuario autenticado  
**Permisos**: Usuario autenticado  
**Headers**: `Authorization: Bearer {token}`  
**Response**: Información del usuario

---

### 👥 Usuarios (`/api/v1/users`)

#### `POST /api/v1/users/create`
**Descripción**: Crear un nuevo usuario  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "username": "string (opcional para USER)",
  "password": "string (opcional para USER)",
  "name": "string",
  "roles": ["USER", "DEALER", "MANAGER", "ADMIN"]
}
```
**Notas**:
- Usuarios tipo USER: username y password opcionales, `is_active = false` por defecto
- Dealers/Managers/Admins: username y password obligatorios, `is_active = true` por defecto
- Solo Admin puede crear usuarios con roles privilegiados

#### `GET /api/v1/users/{user_id}`
**Descripción**: Obtener usuario por ID  
**Permisos**: Usuario autenticado

#### `GET /api/v1/users`
**Descripción**: Listar usuarios con paginación  
**Permisos**: Manager o Admin  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

#### `PUT /api/v1/users/{user_id}`
**Descripción**: Actualizar usuario  
**Permisos**: El mismo usuario o Admin  
**Request Body**:
```json
{
  "name": "string (opcional)",
  "is_active": "boolean (solo Admin)",
  "roles": ["array (solo Admin)"]
}
```

#### `PUT /api/v1/users/{user_id}/roles`
**Descripción**: Actualizar roles de usuario  
**Permisos**: Admin  
**Validaciones**: Si se asignan roles privilegiados (DEALER, MANAGER o ADMIN), el usuario debe tener username y contraseña configurados  
**Request Body**:
```json
{
  "roles": ["USER", "DEALER", "MANAGER", "ADMIN"]
}
```

#### `POST /api/v1/users/{user_id}/activate`
**Descripción**: Activar usuario  
**Permisos**: Admin

#### `POST /api/v1/users/{user_id}/deactivate`
**Descripción**: Desactivar usuario  
**Permisos**: Admin

#### `GET /api/v1/users/stats/overview`
**Descripción**: Obtener estadísticas de usuarios  
**Permisos**: Manager o Admin

#### `DELETE /api/v1/users/{user_id}`
**Descripción**: Eliminar usuario  
**Permisos**: Admin

---

### 🎰 Sesiones (`/api/v1/sessions`)

#### `POST /api/v1/sessions`
**Descripción**: Crear una nueva sesión  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "dealer_id": "string (ID del dealer)",
  "start_time": "datetime",
  "end_time": "datetime (opcional)",
  "jackpot": "int (default: 0)",
  "reik": "int (default: 0)",
  "tips": "int (default: 0)",
  "hourly_pay": "int (default: 0)",
  "comment": "string (opcional)"
}
```
**Validaciones**:
- El `dealer_id` debe ser un usuario con rol Dealer, Manager o Admin

#### `GET /api/v1/sessions/{session_id}`
**Descripción**: Obtener sesión por ID  
**Permisos**: Usuario autenticado

#### `GET /api/v1/sessions`
**Descripción**: Listar sesiones con paginación  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `dealer_id`: string (opcional, filtra por dealer)

#### `GET /api/v1/sessions/active/list`
**Descripción**: Obtener sesiones activas (sin end_time)  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

#### `GET /api/v1/sessions/active/user/{user_id}`
**Descripción**: Obtener todas las sesiones activas de un usuario específico  
**Permisos**: Usuario autenticado  
**Path Parameters**:
- `user_id`: string (ID del usuario/dealer)

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response**:
```json
{
  "sessions": [
    {
      "id": "string",
      "dealer_id": "string",
      "start_time": "datetime",
      "end_time": null,
      "jackpot": 0,
      "reik": 0,
      "tips": 0,
      "hourly_pay": 4000,
      "comment": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "is_active": true,
      "duration_hours": null,
      "total_earnings": 4000
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 100
}
```
**Validaciones**:
- El `user_id` debe existir en la base de datos
- Solo devuelve sesiones sin `end_time` (activas)
- Ordenadas por `start_time` descendente (más recientes primero)

**Ejemplo de uso**:
```python
import requests

url = "http://localhost:8000/api/v1/sessions/active/user/68efb81568be6f15465de821"
headers = {
  'Authorization': 'Bearer {tu_token}'
}

response = requests.get(url, headers=headers)
print(response.json())
```

#### `PUT /api/v1/sessions/{session_id}`
**Descripción**: Actualizar sesión  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "dealer_id": "string (opcional)",
  "start_time": "datetime (opcional)",
  "end_time": "datetime (opcional)",
  "jackpot": "int (opcional)",
  "reik": "int (opcional)",
  "tips": "int (opcional)",
  "hourly_pay": "int (opcional, solo Manager/Admin)",
  "comment": "string (opcional)"
}
```
**Restricción**: Solo Manager y Admin pueden actualizar `hourly_pay`

#### `POST /api/v1/sessions/{session_id}/end`
**Descripción**: Finalizar una sesión activa  
**Permisos**: Dealer, Manager o Admin  
**Request Body** (opcional):
```json
{
  "end_time": "datetime (opcional, usa hora actual si no se proporciona)"
}
```

#### `DELETE /api/v1/sessions/{session_id}`
**Descripción**: Eliminar sesión  
**Permisos**: Manager o Admin

---

### 💰 Transacciones (`/api/v1/transactions`)

#### `POST /api/v1/transactions`
**Descripción**: Crear una nueva transacción  
**Permisos**: Usuario autenticado  
**Request Body**:
```json
{
  "user_id": "string (ID del usuario)",
  "session_id": "string (ID de la sesión)",
  "cantidad": "int",
  "operation_type": "CASH IN | CASH OUT",
  "transaction_media": "DIGITAL | CASH",
  "comment": "string (opcional)"
}
```
**Validaciones**:
- `user_id` debe existir
- `session_id` debe existir y estar activa (abierta)

#### `GET /api/v1/transactions/{transaction_id}`
**Descripción**: Obtener transacción por ID  
**Permisos**: Usuario autenticado

#### `GET /api/v1/transactions`
**Descripción**: Listar transacciones con paginación  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `user_id`: string (opcional, filtra por usuario)
- `session_id`: string (opcional, filtra por sesión)

#### `GET /api/v1/transactions/session/{session_id}`
**Descripción**: Obtener todas las transacciones de una sesión específica  
**Permisos**: Usuario autenticado  
**Path Parameters**:
- `session_id`: string (ID de la sesión)

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response**:
```json
{
  "transactions": [
    {
      "id": "string",
      "user_id": "string",
      "session_id": "string",
      "cantidad": 15000,
      "operation_type": "CASH IN",
      "transaction_media": "DIGITAL",
      "comment": "string",
      "created_at": "datetime",
      "updated_at": "datetime",
      "signed_amount": 15000
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 100
}
```
**Validaciones**:
- El `session_id` debe existir en la base de datos
- Ordenadas por `created_at` descendente (más recientes primero)

**Ejemplo de uso**:
```python
import requests

url = "http://localhost:8000/api/v1/transactions/session/68f01f265b4799044fbfbd66"
headers = {
  'Authorization': 'Bearer {tu_token}'
}

response = requests.get(url, headers=headers)
print(response.json())
```

#### `PUT /api/v1/transactions/{transaction_id}`
**Descripción**: Actualizar transacción  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "cantidad": "int (opcional)",
  "operation_type": "CASH IN | CASH OUT (opcional)",
  "transaction_media": "DIGITAL | CASH (opcional)",
  "comment": "string (opcional)"
}
```
**Nota**: Los campos `user_id` y `session_id` NO se pueden modificar una vez creada la transacción.  
**Restricción**: Si la sesión está cerrada, solo Manager y Admin pueden modificar

#### `DELETE /api/v1/transactions/{transaction_id}`
**Descripción**: Eliminar transacción  
**Permisos**: Dealer, Manager o Admin

---

### 🎁 Bonos (`/api/v1/bonos`)

#### `POST /api/v1/bonos`
**Descripción**: Crear un nuevo bono  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "user_id": "string (ID del usuario)",
  "session_id": "string (ID de la sesión)",
  "value": "int",
  "comment": "string (opcional)"
}
```
**Validaciones**:
- `user_id` debe existir
- `session_id` debe existir y estar activa (abierta)

#### `GET /api/v1/bonos/{bono_id}`
**Descripción**: Obtener bono por ID  
**Permisos**: Usuario autenticado

#### `GET /api/v1/bonos`
**Descripción**: Listar bonos con paginación  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `user_id`: string (opcional, filtra por usuario)
- `session_id`: string (opcional, filtra por sesión)

#### `GET /api/v1/bonos/session/{session_id}`
**Descripción**: Obtener todos los bonos de una sesión específica  
**Permisos**: Usuario autenticado  
**Path Parameters**:
- `session_id`: string (ID de la sesión)

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response**:
```json
{
  "bonos": [
    {
      "id": "string",
      "user_id": "string",
      "session_id": "string",
      "value": 5000,
      "comment": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 100
}
```
**Validaciones**:
- El `session_id` debe existir en la base de datos
- Ordenados por `created_at` descendente (más recientes primero)

**Ejemplo de uso**:
```python
import requests

url = "http://localhost:8000/api/v1/bonos/session/68f01f265b4799044fbfbd66"
headers = {
  'Authorization': 'Bearer {tu_token}'
}

response = requests.get(url, headers=headers)
print(response.json())
```

#### `PUT /api/v1/bonos/{bono_id}`
**Descripción**: Actualizar bono  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "value": "int (opcional)",
  "comment": "string (opcional)"
}
```
**Nota**: Los campos `user_id` y `session_id` NO se pueden modificar una vez creado el bono.  
**Restricción**: Si la sesión está cerrada, solo Manager y Admin pueden modificar

#### `DELETE /api/v1/bonos/{bono_id}`
**Descripción**: Eliminar bono  
**Permisos**: Dealer, Manager o Admin

---

### 🏆 Premios Jackpot (`/api/v1/jackpot-prices`)

#### `POST /api/v1/jackpot-prices`
**Descripción**: Crear un nuevo premio jackpot  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "user_id": "string (ID del usuario)",
  "session_id": "string (ID de la sesión)",
  "value": "int",
  "winner_hand": "string (mano ganadora)",
  "comment": "string (opcional)"
}
```
**Validaciones**:
- `user_id` debe existir
- `session_id` debe existir y estar activa (abierta)

#### `GET /api/v1/jackpot-prices/{jackpot_id}`
**Descripción**: Obtener premio jackpot por ID  
**Permisos**: Usuario autenticado

#### `GET /api/v1/jackpot-prices`
**Descripción**: Listar premios jackpot con paginación  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `user_id`: string (opcional, filtra por usuario)
- `session_id`: string (opcional, filtra por sesión)

#### `GET /api/v1/jackpot-prices/top/winners`
**Descripción**: Obtener top ganadores de jackpot  
**Permisos**: Usuario autenticado  
**Query Parameters**:
- `limit`: int (default: 10)

#### `PUT /api/v1/jackpot-prices/{jackpot_id}`
**Descripción**: Actualizar premio jackpot  
**Permisos**: Dealer, Manager o Admin  
**Request Body**:
```json
{
  "user_id": "string (opcional)",
  "session_id": "string (opcional)",
  "value": "int (opcional)",
  "winner_hand": "string (opcional)",
  "comment": "string (opcional)"
}
```
**Restricción**: Si la sesión está cerrada, solo Manager y Admin pueden modificar

#### `DELETE /api/v1/jackpot-prices/{jackpot_id}`
**Descripción**: Eliminar premio jackpot  
**Permisos**: Dealer, Manager o Admin

---

### 📊 Reportes Diarios (`/api/v1/daily-reports`)

#### `GET /api/v1/daily-reports/date/{report_date}`
**Descripción**: Obtener reporte por fecha  
**Permisos**: Manager o Admin  
**Comportamiento**:
- Si la fecha es HOY (Bogotá): SIEMPRE regenera el reporte (datos en tiempo real)
- Si es fecha pasada: Devuelve existente o genera si no existe
- Los reportes se generan automáticamente desde las sesiones del día
- **NO se pueden crear manualmente**, solo se generan automáticamente
**Respuesta incluye**:
```json
{
  "id": "string",
  "date": "date",
  "reik": "int",
  "jackpot": "int",
  "ganancias": "int",
  "gastos": "int",
  "sessions": ["array de session_ids"],
  "jackpot_wins": [
    {
      "jackpot_win_id": "string",
      "sum": "int"
    }
  ],
  "bonos": [
    {
      "bono_id": "string",
      "sum": "int"
    }
  ],
  "comment": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "net_profit": "int",
  "total_income": "int",
  "is_profitable": "bool",
  "profit_margin": "float"
}
```

#### `GET /api/v1/daily-reports/{report_id}`
**Descripción**: Obtener reporte por ID  
**Permisos**: Manager o Admin

#### `GET /api/v1/daily-reports`
**Descripción**: Listar reportes con paginación  
**Permisos**: Manager o Admin  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `date_from`: date (opcional)
- `date_to`: date (opcional)

#### `GET /api/v1/daily-reports/profitable/list`
**Descripción**: Listar reportes con ganancia positiva  
**Permisos**: Manager o Admin  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

#### `PUT /api/v1/daily-reports/{report_id}`
**Descripción**: Actualizar reporte  
**Permisos**: Manager o Admin  
**Nota importante**: `jackpot_wins` y `bonos` **NO** se pueden modificar manualmente. Son inmutables y se generan automáticamente desde las sesiones.  
**Request Body**:
```json
{
  "reik": "int (opcional)",
  "jackpot": "int (opcional)",
  "ganancias": "int (opcional)",
  "gastos": "int (opcional)",
  "sessions": "array (opcional)",
  "comment": "string (opcional)"
}
```

#### `GET /api/v1/daily-reports/stats/overview`
**Descripción**: Obtener estadísticas de reportes  
**Permisos**: Manager o Admin  
**Query Parameters**:
- `date_from`: date (opcional)
- `date_to`: date (opcional)

#### `DELETE /api/v1/daily-reports/{report_id}`
**Descripción**: Eliminar reporte  
**Permisos**: Manager o Admin

---

## 🔐 Tabla de Permisos por Endpoint

| Recurso | Crear | Leer | Actualizar | Eliminar |
|---------|-------|------|------------|----------|
| **Usuarios** | Dealer+ | Auth | Usuario/Admin | Admin |
| **Sesiones** | Dealer+ | Auth | Dealer+ | Manager+ |
| **Transacciones** | Auth | Auth | Dealer+* | Dealer+ |
| **Bonos** | Dealer+ | Auth | Dealer+* | Dealer+ |
| **Jackpot Prices** | Dealer+ | Auth | Dealer+* | Dealer+ |
| **Daily Reports** | Manager+ | Manager+ | Manager+ | Manager+ |

**Leyenda**:
- `Auth`: Usuario autenticado
- `Dealer+`: Dealer, Manager o Admin
- `Manager+`: Manager o Admin
- `*`: Si la sesión está cerrada, solo Manager+ puede modificar

---

## 📝 Notas Importantes

### Restricciones de Sesiones Cerradas
Una vez que una sesión tiene `end_time` (está cerrada):
- ✅ **Managers y Admins** pueden modificar transacciones, bonos y premios
- ❌ **Dealers** NO pueden modificar datos de sesiones cerradas

### Validaciones Comunes
- Todos los IDs de referencias deben existir en la base de datos
- Las sesiones deben estar activas para crear nuevos registros
- Los usuarios tipo USER pueden tener username/password opcionales
- Dealers, Managers y Admins requieren username y password obligatorios
- **Actualización de roles**: No se puede promover un usuario a rol privilegiado (DEALER, MANAGER, ADMIN) si no tiene username y contraseña configurados
