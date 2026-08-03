---
tags: [gtr, frontend, web, javascript, html, css]
aliases: [Frontend GTR, Portal Web, Landing Page]
status: funcional
progreso: 80
---

# 🌐 Frontend Web Portal

> **TL;DR** — Portal vanilla HTML/CSS/JS con landing page, reservas, login, perfil QR, y paneles admin (red + ESP32). Tema oscuro con glassmorphism.

| Campo | Valor |
|-------|-------|
| Ruta | Raíz `/` + `GTR-*/` |
| Stack | HTML5 · CSS3 · JS ES6+ · qrcode.min.js |
| Diseño | Dark mode · Glassmorphism · Responsivo |
| Backend | Conecta a API en puerto 3001 |

⬅️ [[04_ESP32_Bridge_IoT]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[06_Android_Mobile_App]] ➡️

---

## 📂 Módulos Web

| Módulo | Ruta | Función |
|--------|------|---------|
| **Landing Page** | `/index.html` + `script.js` + `styles.css` | Presentación + formulario de reserva |
| **Login** | `/GTR-Login/` | Inicio de sesión → JWT en localStorage |
| **Perfil + QR** | `/GTR-Profile/` | Datos de usuario + carnet QR digital + gestión de vehículos |
| **Servicios** | `/GTR-Services/` | Catálogo de tarifas y membresías |
| **Experiencia** | `/GTR-Experience/` | Tour interactivo del sistema |
| **Contacto** | `/GTR-Contact/` | Formulario de soporte |

---

## 💻 Paneles Admin

| Panel | Archivo | Función |
|-------|---------|---------|
| **Red** | `admin-network.html` | Dispositivos conectados, bloqueo MAC (`/api/network/block`) |
| **ESP32** | `esp32-panel.html` | Estado barreras, control manual de puertas, LED |

---

## 🎨 Sistema de Estilos

```css
:root {
  --bg-primary: #0b0f19;
  --bg-card: #151c2c;
  --accent-blue: #2563eb;
  --accent-glow: #3b82f6;
  --success-green: #10b981;
  --text-primary: #f8fafc;
  --font-family: 'Inter', system-ui, sans-serif;
}
```

- Responsivo: CSS Grid + Flexbox (320px → 4K)
- Modo oscuro predeterminado
- Gradientes neón azul/esmeralda

---

⬅️ [[04_ESP32_Bridge_IoT]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[06_Android_Mobile_App]] ➡️
