---
tags: [gtr, android, kotlin, mobile, app]
aliases: [App Android GTR, Mobile App, App Móvil]
status: en-desarrollo
progreso: 45
---

# 📱 Android App — Kotlin

> **TL;DR** — App nativa Android en Kotlin para socios: login, parking requests, selección de cajón, garaje de vehículos, carnet QR, display de bienvenida.

| Campo | Valor |
|-------|-------|
| Ruta | `GTR/` |
| Stack | Kotlin · Android SDK 34 · Gradle KTS |
| Paquete | `com.gtr.app` |
| Config | `build.gradle.kts` · `settings.gradle.kts` |

⬅️ [[05_Frontend_Web_Portal]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[07_Notas_de_Integracion]] ➡️

---

## 📂 Estructura

```text
GTR/
├── build.gradle.kts         # Config Gradle raíz
├── settings.gradle.kts      # rootProject.name = "GTR"
└── app/
    └── src/main/
        ├── AndroidManifest.xml
        └── java/com/gtr/app/
            ├── SplashActivity
            ├── LoginActivity
            ├── HomeActivity
            ├── ProfileActivity
            ├── GarageActivity
            ├── ParkingRequestActivity
            └── SettingsActivity
```

---

## 🔐 Permisos

| Permiso | Uso |
|---------|-----|
| `INTERNET` | Comunicación con API REST |
| `ACCESS_NETWORK_STATE` | Detectar WiFi GTR |
| `CAMERA` | Escaneo QR (opcional) |
| `VIBRATE` | Feedback háptico |

---

## ✨ Funcionalidades

- Login con email/password → JWT almacenado en SharedPreferences
- Solicitud de parking (check-in / check-out / helipuerto)
- Mapa de cajones disponibles para selección
- Garaje: gestión de vehículos registrados
- Carnet digital QR de membresía
- Display de bienvenida al escanear (polling `GET /api/scan-event`)

---

## 📦 Proyectos Companion

| Proyecto | Tipo | Función |
|----------|------|---------|
| `GTR-Login/` | Web → Android | Módulo de autenticación |
| `GTR-Profile/` | Web → Android | Perfil + carnet QR |
| `GTR-Services/` | Web → Android | Catálogo de servicios |
| `GTR-Contact/` | Web → Android | Contacto / soporte |
| `GTR-Experience/` | Web → Android | Demo del sistema |

> [!note] Estos son proyectos web separados que complementan la app Android nativa.

---

## 📑 Archivos de Referencia

| Archivo | Descripción |
|---------|------------|
| `ANDROID_STUDIO_INFO.txt` | Config de Android Studio, AGP, JDK 17 |
| `resumen_fixes_scanner_android.txt` | Historial de parches del scanner |

---

⬅️ [[05_Frontend_Web_Portal]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[07_Notas_de_Integracion]] ➡️
