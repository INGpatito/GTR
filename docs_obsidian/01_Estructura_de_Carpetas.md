---
tags: [gtr, estructura, carpetas, directorios]
aliases: [Estructura GTR, Carpetas GTR, Árbol de archivos]
---

# 📁 Estructura de Carpetas

> **TL;DR** — Árbol completo del repositorio GTR con todos los archivos y su propósito.

| Campo | Valor |
|-------|-------|
| Raíz | `/mnt/windows/Linux/GTR` |
| Módulos | 6 (backend, admin-panel, esp32_bridge, frontend, android, docs) |

⬅️ [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[02_Backend_API_NodeJS]] ➡️

---

## 🌳 Árbol del Repositorio

```text
GTR/
├── index.html, script.js, styles.css     # Landing page / Portal web
├── admin-network.html                    # Panel admin de red
├── esp32-panel.html                      # Panel control ESP32
│
├── backend/                              # API REST (Node.js + Express + PostgreSQL)
│   ├── server.js                         # Entry point — Puerto 3001
│   ├── package.json                      # Dependencias npm
│   ├── .env / .env.example               # Variables de entorno
│   ├── ecosystem.config.js               # Config PM2
│   ├── db/
│   │   ├── pool.js                       # Pool PostgreSQL (auto-resolve host)
│   │   ├── init.js                       # Inicialización de DB
│   │   ├── schema.sql                    # Esquema base
│   │   ├── migration_*.sql               # Migraciones (users, vehicles, parking, membership)
│   │   └── consultas.sql                 # Consultas útiles
│   ├── middleware/
│   │   ├── auth.js                       # JWT + Admin API Key
│   │   ├── rateLimiter.js                # Rate limiting
│   │   └── sanitize.js                   # Sanitización inputs
│   ├── routes/
│   │   ├── auth.js                       # POST /api/login
│   │   ├── reservations.js               # CRUD reservaciones
│   │   ├── users.js                      # Gestión usuarios + membresías
│   │   ├── vehicles.js                   # CRUD vehículos
│   │   ├── parking.js                    # Spots + requests + check-in/out
│   │   ├── esp32.js                      # Proxy comandos ESP32
│   │   ├── network.js                    # Hotspot/WiFi/MAC blocking
│   │   └── scanEvents.js                # Eventos de escaneo
│   └── services/
│       └── cryptoService.js              # Generación números de tarjeta
│
├── admin-panel/                          # App Desktop (CustomTkinter)
│   ├── run_admin.py                      # → Panel de administración
│   ├── run_scanner.py                    # → Estación de escaneo
│   ├── member_scanner.py                 # Lógica del escáner QR/tarjeta
│   ├── requirements.txt                  # customtkinter, psycopg2-binary, pyserial, bcrypt
│   ├── config/
│   │   ├── settings.py                   # Config global (auto-resolve DB host)
│   │   └── theme.py                      # Paleta de colores
│   ├── core/
│   │   ├── database.py                   # Conector PostgreSQL directo
│   │   ├── crypto.py                     # Validación tokens QR
│   │   └── email_service.py              # Notificaciones email
│   ├── services/
│   │   ├── member_service.py             # CRUD miembros
│   │   ├── parking_service.py            # Estado cajones
│   │   ├── reservation_service.py        # Gestión reservas
│   │   └── vehicle_service.py            # Gestión vehículos
│   ├── ui/
│   │   ├── widgets.py                    # Componentes UI custom
│   │   ├── admin/                        # Tabs: app, members, parking, activity, security, sidebar
│   │   └── scanner/                      # Ventanas: app, profile_view, sidebar
│   └── utils/
│       ├── esp32_controller.py           # Control Serial/HTTP de barrera
│       ├── cars_api.py                   # API marcas/modelos
│       ├── mock_server.py                # Servidor de pruebas
│       └── sound.py                      # Alertas sonoras
│
├── esp32_bridge/                         # Firmware IoT (Arduino C++)
│   ├── esp32_bridge.ino                  # Firmware principal dual-gate (13.6KB)
│   ├── sp32.ino                          # Versión alternativa (9.6KB)
│   └── ESP32.ino                         # Boceto base
│
├── GTR/                                  # App Android (Kotlin, SDK 34)
│   ├── build.gradle.kts                  # Config Gradle raíz
│   ├── settings.gradle.kts               # rootProject.name = "GTR"
│   └── app/src/main/                     # Código fuente (com.gtr.app)
│
├── GTR-Login/                            # Módulo web: inicio de sesión
├── GTR-Profile/                          # Módulo web: perfil + QR
├── GTR-Services/                         # Módulo web: catálogo servicios
├── GTR-Experience/                       # Módulo web: demo/tour
├── GTR-Contact/                          # Módulo web: contacto/soporte
│
├── docs_obsidian/                        # Esta documentación
│
├── deploy.sh                             # Deploy automatizado bash
├── deploy_orangepi.py                    # Deploy SSH a Orange Pi
├── deploy_esp32_panel.py                 # Deploy panel ESP32
├── fix_hotspot.py                        # Configurar hotspot WiFi
├── get_logs.py                           # Extracción de logs
├── test_api.js                           # Tests de API
├── DEPLOY_ORANGE_PI.md                   # Manual de deploy
├── ANDROID_STUDIO_INFO.txt               # Config Android Studio
├── resumen_fixes_esp32.txt               # Historial parches ESP32
└── resumen_fixes_scanner_android.txt     # Historial parches scanner
```

---

## 📊 Resumen por Módulo

| Carpeta | Stack | Doc |
|---------|-------|-----|
| `backend/` | Node.js + Express + PostgreSQL | [[02_Backend_API_NodeJS]] |
| `admin-panel/` | Python + CustomTkinter | [[03_Admin_Panel_Python]] |
| `esp32_bridge/` | Arduino C++ (ESP32) | [[04_ESP32_Bridge_IoT]] |
| `*.html` / `GTR-*/` | HTML/CSS/JS Vanilla | [[05_Frontend_Web_Portal]] |
| `GTR/` | Kotlin + Android SDK 34 | [[06_Android_Mobile_App]] |
| `deploy*.py` / `*.sh` | Python / Bash | [[07_Notas_de_Integracion]] |

---

⬅️ [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[02_Backend_API_NodeJS]] ➡️
