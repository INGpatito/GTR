---
tags: [gtr, admin, python, customtkinter, scanner, desktop]
aliases: [Admin Panel GTR, Panel Admin, Scanner GTR]
status: funcional
progreso: 85
---

# 💻 Admin Panel — Python Desktop

> **TL;DR** — App de escritorio CustomTkinter con dos modos: Panel Admin (gestión de miembros/parking/actividad) y Scanner (escaneo QR/tarjeta + control de barrera).

| Campo | Valor |
|-------|-------|
| Ruta | `admin-panel/` |
| Stack | Python 3.11+ · CustomTkinter · psycopg2 · pyserial |
| Modos | `python run_admin.py` (admin) · `python run_scanner.py` (scanner) |
| Conexión DB | PostgreSQL directo (psycopg2) + API REST (requests) |

⬅️ [[02_Backend_API_NodeJS]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[04_ESP32_Bridge_IoT]] ➡️

---

## 📂 Estructura

```text
admin-panel/
├── run_admin.py              # → Panel Admin
├── run_scanner.py            # → Escáner
├── member_scanner.py         # Lógica de escaneo QR/tarjeta (28KB)
├── requirements.txt          # customtkinter, psycopg2-binary, pyserial, bcrypt
├── config/
│   ├── settings.py           # Config global (auto-resolve DB host)
│   └── theme.py              # Paleta de colores
├── core/
│   ├── database.py           # Conector PostgreSQL
│   ├── crypto.py             # Validación tokens QR
│   └── email_service.py      # Envío de emails
├── services/
│   ├── member_service.py     # CRUD miembros
│   ├── parking_service.py    # Estado de cajones
│   ├── reservation_service.py # Gestión de reservas
│   └── vehicle_service.py    # Gestión de vehículos
├── ui/
│   ├── widgets.py            # Componentes UI custom
│   ├── admin/                # Panel Admin
│   │   ├── app.py            # Ventana principal (CTk)
│   │   ├── members_tab.py    # Gestión de miembros
│   │   ├── parking_tab.py    # Mapa de cajones
│   │   ├── activity_tab.py   # Log de actividad
│   │   ├── security_dialog.py # Bloqueo de accesos
│   │   └── sidebar.py        # Navegación lateral
│   └── scanner/              # Escáner
│       ├── app.py            # Ventana fullscreen
│       ├── profile_view.py   # Perfil del miembro escaneado
│       └── sidebar.py        # Estado de conexión
└── utils/
    ├── esp32_controller.py   # Control barrera Serial/HTTP
    ├── cars_api.py           # Autocompletado marcas/modelos
    ├── mock_server.py        # Servidor de pruebas
    └── sound.py              # Alertas sonoras
```

---

## 🔧 Componentes Principales

| Componente | Archivo | Función |
|-----------|---------|---------|
| **Scanner QR** | `member_scanner.py` | Lee QR/tarjeta → valida → muestra perfil → abre barrera |
| **Mapa Parking** | `parking_tab.py` | Grid visual de 24 cajones (🟢libre 🔴ocupado 🟡reservado) |
| **Miembros** | `members_tab.py` | Alta/baja/edición + emisión de QR |
| **Actividad** | `activity_tab.py` | Log de entradas/salidas en tiempo real |
| **Seguridad** | `security_dialog.py` | Bloqueo instantáneo de usuarios/MACs |
| **ESP32 Control** | `esp32_controller.py` | Comandos via Serial (`/dev/ttyUSB0`) o HTTP |

---

## 🔄 Flujo del Scanner

1. Escucha entrada Serial/teclado
2. Valida firma del token con `core/crypto.py`
3. Consulta membresía via `services/member_service.py`
4. Si válido → muestra perfil en `profile_view.py` + beep `sound.py`
5. Abre barrera via `esp32_controller.py`
6. Registra evento en `POST /api/scan-event`

---

## 🎨 Tema (`config/theme.py`)

| Token | Color | Uso |
|-------|-------|-----|
| Fondo | `#0F172A` | Superficie principal |
| Tarjeta | `#1E293B` | Cards y paneles |
| Acento | `#3B82F6` | Botones primarios |
| Éxito | `#10B981` | Acceso permitido |
| Error | `#EF4444` | Acceso denegado |
| Texto | `#F8FAFC` | Texto principal |

---

⬅️ [[02_Backend_API_NodeJS]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[04_ESP32_Bridge_IoT]] ➡️
