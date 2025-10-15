# Documentación de Schemas de Base de Datos

## 📋 Índice de Schemas
- [USER](#1-schema-user)
- [SESSION](#2-schema-session)
- [TRANSACTION](#3-schema-transaction)
- [DAILY REPORT](#4-schema-daily-report)
- [BONO](#5-schema-bono)
- [JACKPOT PRICE](#6-schema-jackpot-price)

---

## 1. Schema: USER

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "user_id": "usr_507f1f77bcf86cd799439011",
  "nombre": "Juan Pérez",
  "creation_time": ISODate("2025-01-06T21:00:00Z"),
  "password": "$2b$12$e7hTt2xQ8q9wE3rT5yU6iO9pA2sD4fG7hJ8kL1mN3oP6qR9tU2vW5xY8zA1bC4eF",
  "role": "DEALER",
  "active": true
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **user_id** | String | Identificador único del usuario (PK) | Requerido, único |
| **nombre** | String | Nombre completo del usuario | Requerido |
| **creation_time** | DateTime | Fecha y hora de creación del usuario | Requerido, automático |
| **password** | String | Contraseña hasheada (bcrypt) | Requerido, min 8 caracteres |
| **role** | String | Rol del usuario | Enum: "USER", "DEALER", "ADMIN", "MANAGER" |
| **active** | Boolean | Estado de activación de la cuenta | Requerido, default: true |

### Validaciones
- `role` solo puede ser: **"USER"**, **"DEALER"**, **"ADMIN"**, **"MANAGER"**
- `password` debe ser hasheada con bcrypt antes de almacenar
- `user_id` debe ser único en toda la colección

### Índices Recomendados
```javascript
// Índice único en user_id
db.users.createIndex({ "user_id": 1 }, { unique: true })

// Índice en role para consultas rápidas
db.users.createIndex({ "role": 1 })

// Índice en estado activo
db.users.createIndex({ "active": 1 })

// Índice de texto para búsqueda por nombre
db.users.createIndex({ "nombre": "text" })
```

---

## 2. Schema: SESSION

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "session_id": "ses_507f1f77bcf86cd799439012",
  "dealer_id": "usr_507f1f77bcf86cd799439011",
  "start_time": ISODate("2025-10-13T08:00:00Z"),
  "end_time": ISODate("2025-10-13T16:00:00Z"),
  "jackpot": 50000,
  "reik": 15000,
  "tips": 2500,
  "hourly_pay": 5000,
  "comment": "Sesión del turno de la mañana"
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **session_id** | String | Identificador único de la sesión (PK) | Requerido, único |
| **dealer_id** | String | ID del dealer asignado (FK → USER) | Requerido |
| **start_time** | DateTime | Hora de inicio de la sesión | Requerido |
| **end_time** | DateTime | Hora de finalización de la sesión | Opcional, null si sesión activa |
| **jackpot** | Integer | Monto del jackpot acumulado | Requerido, >= 0 |
| **reik** | Integer | Monto de reik | Requerido, >= 0 |
| **tips** | Integer | Propinas recibidas | Requerido, >= 0 |
| **hourly_pay** | Integer | Pago por hora | Requerido, >= 0 |
| **comment** | String | Comentario adicional sobre la sesión | Opcional |

### Validaciones
- `dealer_id` debe existir en la colección USER con role "DEALER"
- `end_time` debe ser posterior a `start_time` (si existe)
- Todos los valores monetarios deben ser >= 0

### Índices Recomendados
```javascript
// Índice único en session_id
db.sessions.createIndex({ "session_id": 1 }, { unique: true })

// Índice en dealer_id para búsquedas por dealer
db.sessions.createIndex({ "dealer_id": 1 })

// Índice compuesto para consultas de rango de fechas
db.sessions.createIndex({ "start_time": -1, "end_time": -1 })

// Índice para sesiones activas
db.sessions.createIndex({ "end_time": 1 })
```

---

## 3. Schema: TRANSACTION

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439013"),
  "transaction_id": "txn_507f1f77bcf86cd799439013",
  "user_id": "usr_507f1f77bcf86cd799439011",
  "session_id": "ses_507f1f77bcf86cd799439012",
  "cantidad": 10000,
  "operation_type": "IN",
  "transaction_media": "DIGITAL",
  "comment": "Pago de cliente VIP"
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **transaction_id** | String | Identificador único de la transacción (PK) | Requerido, único |
| **user_id** | String | ID del usuario que realizó la transacción (FK → USER) | Requerido |
| **session_id** | String | ID de la sesión asociada (FK → SESSION) | Requerido |
| **cantidad** | Integer/Float | Monto de la transacción | Requerido, > 0 |
| **operation_type** | String | Tipo de operación | Enum: "IN", "OUT" |
| **transaction_media** | String | Medio de la transacción | Enum: "DIGITAL", "CASH" |
| **comment** | String | Comentario sobre la transacción | Opcional |

### Validaciones
- `operation_type` solo puede ser: **"IN"** (entrada) o **"OUT"** (salida)
- `transaction_media` solo puede ser: **"DIGITAL"** o **"CASH"**
- `user_id` debe existir en la colección USER
- `session_id` debe existir en la colección SESSION
- `cantidad` debe ser mayor a 0

### Índices Recomendados
```javascript
// Índice único en transaction_id
db.transactions.createIndex({ "transaction_id": 1 }, { unique: true })

// Índice en user_id para búsquedas por usuario
db.transactions.createIndex({ "user_id": 1 })

// Índice en session_id para búsquedas por sesión
db.transactions.createIndex({ "session_id": 1 })

// Índice compuesto para reportes
db.transactions.createIndex({ "operation_type": 1, "transaction_media": 1 })
```

---

## 4. Schema: DAILY REPORT

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439014"),
  "daily_report_id": "rpt_507f1f77bcf86cd799439014",
  "reik": 45000,
  "date": ISODate("2025-10-13T00:00:00Z"),
  "jackpot": 150000,
  "ganancias": 200000,
  "gastos": 80000,
  "sessions": ["ses_507f1f77bcf86cd799439012", "ses_507f1f77bcf86cd799439013",...],
  "comment": "Día con alta actividad"
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **daily_report_id** | String | Identificador único del reporte diario (PK) | Requerido, único |
| **reik** | Integer | Monto total de reik del día | Requerido, >= 0 |
| **date** | DateTime | Fecha del reporte | Requerido, único por día |
| **jackpot** | Integer | Monto total del jackpot | Requerido, >= 0 |
| **ganancias** | Integer | Ganancias totales del día | Requerido, >= 0 |
| **gastos** | Integer | Gastos totales del día | Requerido, >= 0 |
| **sessions** | Array[String] | Lista de IDs de sesiones del día (FK → SESSION) | Opcional, array de session_id |
| **comment** | String | Comentario adicional sobre el día | Opcional |

### Validaciones
- `date` debe ser única (un reporte por día)
- Todos los valores monetarios deben ser >= 0
- `ganancias` - `gastos` = beneficio neto (calculado)
- Cada `session_id` en `sessions` debe existir en la colección SESSION

### Índices Recomendados
```javascript
// Índice único en daily_report_id
db.daily_reports.createIndex({ "daily_report_id": 1 }, { unique: true })

// Índice único en date para evitar reportes duplicados
db.daily_reports.createIndex({ "date": 1 }, { unique: true })

// Índice descendente para obtener reportes recientes
db.daily_reports.createIndex({ "date": -1 })

// Índice en sessions para búsquedas por sesión
db.daily_reports.createIndex({ "sessions": 1 })
```

---

## 5. Schema: BONO

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439015"),
  "bono_id": "bon_507f1f77bcf86cd799439015",
  "user_id": "usr_507f1f77bcf86cd799439011",
  "session_id": "ses_507f1f77bcf86cd799439012",
  "value": 5000,
  "comment": "Bono por desempeño excepcional"
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **bono_id** | String | Identificador único del bono (PK) | Requerido, único |
| **user_id** | String | ID del usuario receptor del bono (FK → USER) | Requerido |
| **session_id** | String | ID de la sesión asociada (FK → SESSION) | Requerido |
| **value** | Integer/Float | Valor del bono | Requerido, > 0 |
| **comment** | String | Comentario o motivo del bono | Opcional |

### Validaciones
- `user_id` debe existir en la colección USER
- `session_id` debe existir en la colección SESSION
- `value` debe ser mayor a 0

### Índices Recomendados
```javascript
// Índice único en bono_id
db.bonos.createIndex({ "bono_id": 1 }, { unique: true })

// Índice en user_id para búsquedas por usuario
db.bonos.createIndex({ "user_id": 1 })

// Índice en session_id para búsquedas por sesión
db.bonos.createIndex({ "session_id": 1 })

// Índice compuesto para reportes de bonos por usuario y sesión
db.bonos.createIndex({ "user_id": 1, "session_id": 1 })
```

---

## 6. Schema: JACKPOT PRICE

### Estructura del Documento
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439016"),
  "jackpot_price_id": "jkp_507f1f77bcf86cd799439016",
  "user_id": "usr_507f1f77bcf86cd799439011",
  "session_id": "ses_507f1f77bcf86cd799439012",
  "value": 50000,
  "winner_hand": "Royal Flush",
  "comment": "Jackpot ganado en mesa 3"
}
```

### Campos
| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| **jackpot_price_id** | String | Identificador único del premio jackpot (PK) | Requerido, único |
| **user_id** | String | ID del usuario ganador (FK → USER) | Requerido |
| **session_id** | String | ID de la sesión donde se ganó (FK → SESSION) | Requerido |
| **value** | Integer/Float | Valor del premio jackpot | Requerido, > 0 |
| **winner_hand** | String | Mano ganadora | Opcional |
| **comment** | String | Comentario adicional sobre el premio | Opcional |

### Validaciones
- `user_id` debe existir en la colección USER
- `session_id` debe existir en la colección SESSION
- `value` debe ser mayor a 0

### Índices Recomendados
```javascript
// Índice único en jackpot_price_id
db.jackpot_prices.createIndex({ "jackpot_price_id": 1 }, { unique: true })

// Índice en user_id para búsquedas por ganador
db.jackpot_prices.createIndex({ "user_id": 1 })

// Índice en session_id para búsquedas por sesión
db.jackpot_prices.createIndex({ "session_id": 1 })

// Índice en value para ordenar por premios mayores
db.jackpot_prices.createIndex({ "value": -1 })
```

---

## 🔗 Relaciones entre Schemas

```
USER (1) ──┬─> (N) SESSION (dealer_id)
           ├─> (N) TRANSACTION (user_id)
           ├─> (N) BONO (user_id)
           └─> (N) JACKPOT_PRICE (user_id)

SESSION (1) ──┬─> (N) TRANSACTION (session_id)
              ├─> (N) BONO (session_id)
              └─> (N) JACKPOT_PRICE (session_id)

DAILY_REPORT (1) ──> (N) SESSION (sessions[])
```

### Descripción de Relaciones
- Un **USER** puede tener múltiples **SESSION** (si es DEALER)
- Un **USER** puede tener múltiples **TRANSACTION**
- Un **USER** puede recibir múltiples **BONO**
- Un **USER** puede ganar múltiples **JACKPOT_PRICE**
- Una **SESSION** puede tener múltiples **TRANSACTION**
- Una **SESSION** puede tener múltiples **BONO**
- Una **SESSION** puede tener múltiples **JACKPOT_PRICE**
- Un **DAILY_REPORT** puede contener múltiples **SESSION** (a través de sessions[])

---

## 🔐 Consideraciones de Seguridad

### Contraseñas (USER)
- **Hashing**: Siempre usar bcrypt con salt automático
- **Validación**: Mínimo 8 caracteres, incluir mayúsculas, minúsculas y números
- **Almacenamiento**: Nunca almacenar contraseñas en texto plano

### Roles (USER)
- **USER**: Usuario básico del sistema
- **DEALER**: Crupier/dealer que maneja sesiones
- **ADMIN**: Administrador con acceso completo
- **MANAGER**: Gerente con acceso a reportes y gestión

### Validación de Foreign Keys
- Siempre validar que los IDs referenciados existan antes de crear registros
- Implementar validación en capa de servicio

---

## 📊 Consultas Comunes

### Obtener todas las transacciones de una sesión
```javascript
db.transactions.find({ "session_id": "ses_507f1f77bcf86cd799439012" })
```

### Calcular total de propinas de un dealer
```javascript
db.sessions.aggregate([
  { $match: { "dealer_id": "usr_507f1f77bcf86cd799439011" } },
  { $group: { _id: null, total_tips: { $sum: "$tips" } } }
])
```

### Obtener balance diario (ganancias - gastos)
```javascript
db.daily_reports.aggregate([
  {
    $project: {
      date: 1,
      balance: { $subtract: ["$ganancias", "$gastos"] }
    }
  }
])
```

### Listar top ganadores de jackpot
```javascript
db.jackpot_prices.aggregate([
  {
    $lookup: {
      from: "users",
      localField: "user_id",
      foreignField: "user_id",
      as: "user_info"
    }
  },
  { $sort: { "value": -1 } },
  { $limit: 10 }
])
```

### Obtener todas las sesiones de un día específico
```javascript
db.daily_reports.findOne({ "date": ISODate("2025-10-13T00:00:00Z") })
```

### Buscar reportes que contengan una sesión específica
```javascript
db.daily_reports.find({ "sessions": "ses_507f1f77bcf86cd799439012" })
```

### Agregar una sesión a un reporte diario
```javascript
db.daily_reports.updateOne(
  { "daily_report_id": "**rpt_507f1f77bcf86cd799439014**" },
  { $push: { "sessions": "ses_507f1f77bcf86cd799439015" } }
)
```

### Obtener reporte con detalles de todas sus sesiones
```javascript
db.daily_reports.aggregate([
  { $match: { "date": ISODate("2025-10-13T00:00:00Z") } },
  {
    $lookup: {
      from: "sessions",
      localField: "sessions",
      foreignField: "session_id",
      as: "session_details"
    }
  }
])
```

---

## 🚀 Próximos Pasos

1. **Implementar validación de Foreign Keys** en servicios
2. **Crear endpoints REST** para cada schema
3. **Implementar autenticación JWT** basada en roles
4. **Crear sistema de auditoría** para cambios críticos
5. **Implementar backup automático** de reportes diarios
6. **Dashboard de análisis** con métricas en tiempo real
7. **Notificaciones** para jackpots y bonos
8. **Rate limiting** en endpoints sensibles
