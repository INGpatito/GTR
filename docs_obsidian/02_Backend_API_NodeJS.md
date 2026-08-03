---
tags: [gtr, backend, nodejs, api, express, postgresql]
aliases: [Backend GTR, API GTR, API Parking]
status: funcional
progreso: 95
---

# 🖥️ Backend API — Node.js + PostgreSQL

> **TL;DR** — API REST con Express + PostgreSQL. Auth JWT + bcrypt. 38+ endpoints para parking, usuarios, vehículos, ESP32, red y escaneo.

| Campo | Valor |
|-------|-------|
| Ruta | `backend/` |
| Entry point | `server.js` |
| Puerto | `3001` |
| DB | PostgreSQL (`parking_gtr`) :5432 |
| Auth | JWT (7d) + bcrypt (12 rounds) + Admin API Key |
| Dependencias | express, pg, jsonwebtoken, bcrypt, helmet, cors, rate-limit, dotenv |

⬅️ [[01_Estructura_de_Carpetas]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[03_Admin_Panel_Python]] ➡️

---

## 📡 Endpoints API

### 🔑 Autenticación
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `POST` | `/api/login` | Pública | Login → JWT |

### 📋 Reservaciones
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `POST` | `/api/reservations` | Pública | Crear reservación + usuario |
| `GET` | `/api/reservations` | Admin | Listar (filtros, paginación) |
| `GET` | `/api/reservations/:id` | Admin | Obtener por ID |
| `PATCH` | `/api/reservations/:id` | Admin | Cambiar estado |

### 👤 Usuarios
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `GET` | `/api/user/:id` | JWT | Info + tarjeta virtual |
| `PUT` | `/api/user/:id` | JWT | Editar nombre/teléfono |
| `PUT` | `/api/user/:id/password` | JWT | Cambiar contraseña |
| `GET` | `/api/user/:id/stats` | JWT | Estadísticas |
| `PATCH` | `/api/user/:id/service` | JWT | Servicio preferido |
| `PATCH` | `/api/user/:id/membership` | JWT | Nivel de membresía |
| `GET` | `/api/user/:id/activity` | JWT | Últimas 10 actividades |

### 🚗 Vehículos
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `GET` | `/api/user/:id/vehicles` | JWT | Listar |
| `POST` | `/api/user/:id/vehicles` | JWT | Agregar (límite por membresía) |
| `PUT` | `/api/user/:id/vehicles/:vid` | JWT | Editar |
| `DELETE` | `/api/user/:id/vehicles/:vid` | JWT | Eliminar |

### 🅿️ Estacionamiento
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `GET` | `/api/parking/spots` | Pública | 24 cajones + estado |
| `GET` | `/api/parking/spots/:floor` | Pública | Cajones por piso |
| `GET` | `/api/parking/heliport` | Pública | Estado helipuerto |
| `POST` | `/api/parking/request` | Pública | Solicitar check-in/out/heliport |
| `GET` | `/api/parking/request/pending` | Pública | Pendientes (admin) |
| `GET` | `/api/parking/request/:userId/status` | Pública | Estado de solicitud |
| `PATCH` | `/api/parking/request/:id/approve` | Pública | Aprobar |
| `PATCH` | `/api/parking/request/:id/reject` | Pública | Rechazar |
| `POST` | `/api/parking/spot/select` | Pública | Seleccionar cajón |
| `POST` | `/api/parking/checkout/:spotId` | Pública | Liberar cajón |

### 📡 ESP32
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `POST` | `/api/esp32/register` | Pública | ESP32 registra su IP |
| `GET` | `/api/esp32/status` | Pública | Estado de conexión |
| `GET` | `/api/esp32/heartbeat` | Pública | Ping + info |
| `POST` | `/api/esp32/command` | Pública | Proxy de comandos |

### 🌐 Red
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `GET` | `/api/network/status` | Pública | Hotspot/WiFi/SSID/IP |
| `POST` | `/api/network/toggle-mode` | Pública | auto/manual-wifi/manual-hotspot |
| `GET` | `/api/network/clients` | Pública | Clientes del hotspot |
| `POST` | `/api/network/block` | Pública | Bloquear/desbloquear MAC |

### 📸 Scan Events
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `POST` | `/api/scan-event` | Admin | Registrar escaneo |
| `POST` | `/api/scan-event/card` | Pública | Resolver tarjeta → miembro |
| `GET` | `/api/scan-event` | Pública | Último evento (<30s) |
| `DELETE` | `/api/scan-event` | Pública | Limpiar evento |

### ❤️ Health
| Método | Ruta | Auth | Descripción |
|--------|------|------|------------|
| `GET` | `/api/health` | Pública | Estado servidor + DB |

---

## 🗃️ Base de Datos

### Enums
| Tipo | Valores |
|------|---------|
| `reservation_status` | pending, confirmed, cancelled, completed |
| `vehicle_type` | sports, suv, sedan, convertible, exotic |
| `service_type` | valet, monthly, event, concierge, fleet |

### `reservations`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | — |
| user_id | INT FK → users | — |
| service | service_type | — |
| vehicle | vehicle_type | default: sports |
| arrival_date / arrival_time | DATE / TIME | — |
| message | TEXT | opcional |
| status | reservation_status | default: pending |
| lang | CHAR(2) | default: en |
| ip_address | VARCHAR(45) | IP del cliente |
| created_at / updated_at | TIMESTAMPTZ | auto |

### `users`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | — |
| full_name | VARCHAR(120) | — |
| email | VARCHAR(255) UNIQUE | lowercase |
| phone | VARCHAR(30) | — |
| password_hash | TEXT | bcrypt 12 rounds |
| preferred_service | service_type | default: valet |
| status | VARCHAR(20) | pending/active/confirmed/completed |
| membership_tier | VARCHAR(20) | none/silver/gold/platinum |
| created_at / updated_at | TIMESTAMPTZ | auto |

### `user_vehicles`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | — |
| user_id | INT FK → users | CASCADE |
| nickname | VARCHAR(60) | — |
| brand / model | VARCHAR(60) | — |
| year | SMALLINT | — |
| color | VARCHAR(30) | — |
| plate | VARCHAR(20) | — |
| vehicle | vehicle_type | default: sports |
| is_primary | BOOLEAN | — |

> [!tip] Límite por membresía
> none=0, silver=1, gold=2, platinum=3 vehículos máximo.

### `parking_spots`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | — |
| spot_number | INT | 1-24 |
| floor | INT | 1-3 (0=helipuerto) |
| spot_label | VARCHAR(10) | P1-01, HELI-01 |
| status | VARCHAR(20) | available/occupied |
| occupied_by_user_id | INT FK | — |
| occupied_by_vehicle_id | INT FK | — |
| occupied_at | TIMESTAMPTZ | — |

> [!note] Distribución
> 24 cajones (3 pisos × 8) + 1 helipuerto (floor=0).

### `parking_requests`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | — |
| user_id | INT FK → users | CASCADE |
| vehicle_id | INT FK → user_vehicles | — |
| request_type | VARCHAR(20) | check_in/check_out/heliport |
| status | VARCHAR(20) | pending/approved/rejected/completed |
| spot_id | INT FK → parking_spots | — |

---

## ⚙️ Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|------------|
| `DB_HOST` | auto | auto = resolver entre 4 IPs candidatas |
| `DB_PORT` | 5432 | Puerto PostgreSQL |
| `DB_USER` | postgres | — |
| `DB_PASSWORD` | — | Requerida |
| `DB_NAME` | parking_gtr | — |
| `PORT` | 3001 | Puerto del servidor |
| `CORS_ORIGINS` | — | Orígenes separados por coma |
| `ADMIN_API_KEY` | — | Key para endpoints admin |
| `JWT_SECRET` | — | Secreto para firmar tokens |

> [!warning] Auto-resolución de host
> `pool.js` prueba: `10.42.0.1` → `192.168.100.16` → `100.89.43.30` → `192.168.100.61` → fallback `127.0.0.1`

---

## 🚀 Comandos

```bash
cd backend
npm install        # Instalar dependencias
npm start          # node server.js
npm run dev        # node --watch server.js
npm run db:init    # node db/init.js
```

---

⬅️ [[01_Estructura_de_Carpetas]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[03_Admin_Panel_Python]] ➡️
