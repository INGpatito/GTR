---
tags: [gtr, esp32, iot, arduino, hardware, barrera]
aliases: [ESP32 Bridge, IoT Gateway, Firmware GTR]
status: funcional
progreso: 90
---

# 📡 ESP32 Bridge — Firmware Dual Gate

> **TL;DR** — Firmware Arduino C++ para ESP32 que controla 2 puertas (entrada/salida) con servos, sensores IR y ultrasónicos. Servidor HTTP en puerto 80 + comandos serial.

| Campo | Valor |
|-------|-------|
| Ruta | `esp32_bridge/` |
| Archivo principal | `esp32_bridge.ino` (13.6KB) |
| Stack | Arduino C++ · ESP32Servo · WiFi · WebServer · HTTPClient |
| WiFi SSID | `GTR` (hotspot Orange Pi) |
| WebServer | Puerto 80 |
| Registro | `POST http://10.42.0.1:3000/api/esp32/register` |

> [!warning] El firmware tiene hardcodeado puerto 3000, pero `.env` define PORT=3001. Verificar que coincidan.

⬅️ [[03_Admin_Panel_Python]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[05_Frontend_Web_Portal]] ➡️

---

## 🔌 Mapeo de Pines

| Componente | Pin | Tipo | Función |
|-----------|-----|------|---------|
| Servo Entrada | GPIO 18 | PWM OUT | Puerta entrada (90°=abierto, 180°=cerrado) |
| Servo Salida | GPIO 19 | PWM OUT | Puerta salida (90°=abierto, 180°=cerrado) |
| IR Entrada | GPIO 16 | Digital IN | Detecta vehículo → abre entrada |
| IR Salida | GPIO 23 | Digital IN | Detecta paso → cierra salida |
| US Trig Entrada | GPIO 4 | Digital OUT | Ultrasonido trigger (entrada) |
| US Echo Entrada | GPIO 17 | Digital IN | Ultrasonido echo (entrada) |
| US Trig Salida | GPIO 5 | Digital OUT | Ultrasonido trigger (salida) |
| US Echo Salida | GPIO 12 | Digital IN | Ultrasonido echo (salida) |
| LED Estado | GPIO 2 | Digital OUT | Indicador onboard |

---

## 🌐 Endpoints HTTP (Puerto 80)

| Ruta | Función |
|------|---------|
| `GET /api/entrada/abrir` | Servo entrada → 90° |
| `GET /api/entrada/cerrar` | Servo entrada → 180° |
| `GET /api/salida/abrir` | Servo salida → 90° |
| `GET /api/salida/cerrar` | Servo salida → 180° |
| `GET /api/led?state=0\|1` | Control LED |
| `GET /api/status` | Estado puertas + WiFi |
| `GET /api/heartbeat` | Ping (alive, uptime) |
| `GET /api/info` | Info completa (IP, MAC, RSSI, heap) |

---

## 💻 Comandos Serial (115200 baud)

| Comando | Acción |
|---------|--------|
| `e_abrir` | Abre entrada |
| `e_cerrar` | Cierra entrada |
| `s_abrir` | Abre salida |
| `s_cerrar` | Cierra salida |
| `ping` | Responde `{"status":"pong"}` |
| `LED:0` / `LED:1` | Control LED |

> [!tip] También acepta JSON: `{"command":"e_abrir"}`

---

## ⚡ Lógica Automática de Puertas

**Entrada:**
1. Sensor IR (GPIO 16) detecta vehículo → abre servo entrada
2. Ultrasónico confirma paso (<10cm) → espera que se despeje (≥10cm)
3. Delay 800ms → cierra servo entrada

**Salida:**
1. Ultrasónico salida detecta vehículo (<10cm) → abre servo salida
2. Sensor IR (GPIO 23) detecta paso → espera que se despeje
3. Delay 800ms → cierra servo salida

---

## 📡 Conectividad WiFi

- Conecta a SSID `GTR` al arrancar
- Registra IP con el backend: `POST /api/esp32/register`
- Reconexión WiFi cada 15s si se pierde
- Re-registro cada 10s si no confirmado

> [!note] El backend hace heartbeat *hacia* el ESP32 (`GET /api/heartbeat`), no al revés.

---

## 📄 Archivos

| Archivo | Tamaño | Descripción |
|---------|--------|------------|
| `esp32_bridge.ino` | 13.6KB | Firmware principal dual-gate |
| `sp32.ino` | 9.6KB | Versión alternativa |
| `ESP32.ino` | Mínimo | Boceto de pruebas |

---

⬅️ [[03_Admin_Panel_Python]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[05_Frontend_Web_Portal]] ➡️
