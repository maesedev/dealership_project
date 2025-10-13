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

## Endpoints Disponibles

- `GET /` - Hello World
- `GET /api/v1/health` - Health check
- `GET /docs` - Documentación interactiva

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
