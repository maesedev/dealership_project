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
- ✅ Login con email y contraseña
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
- `POST /api/v1/auth/login` - Login con email y contraseña
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

### Proteger Endpoints con Autenticación

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
