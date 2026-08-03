---
kanban-plugin: basic
tags: [gtr, kanban, tareas, estado]
aliases: [Kanban GTR, Estado del Proyecto, Tareas GTR]
---

# 📋 Kanban — Estado del Proyecto

⬅️ [[08_Obsidian_Dataview_Queries]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]]

---

## 🔴 Backlog

- [ ] ALPR/LPR: Reconocimiento óptico de placas con IA en cámara de entrada #backlog
- [ ] Pagos en línea: Pasarela de cobro en app móvil #mobile
- [ ] Analytics: Dashboard de ocupación por hora/día #backend
- [ ] Reportes PDF: Generación automática de ingresos desde Admin Panel #admin

## 🟡 En Progreso

- [ ] ESP32: Reconexión WiFi robusta cuando el hotspot parpadea #esp32
- [ ] Backend: Pruebas de carga del pool PostgreSQL en Orange Pi #backend
- [ ] Frontend: Micro-animaciones e interacciones en el portal web #frontend
- [ ] Android: Activities de parking request y selección de cajón #android

## 🟢 Completado

- [x] Seguridad Express: Helmet + CORS + sanitize + rate-limit [[02_Backend_API_NodeJS]] #backend
- [x] Scanner Python: Lectura QR/tarjeta con feedback sonoro [[03_Admin_Panel_Python]] #admin
- [x] ESP32 Dual Gate: HTTP + Serial bidireccional [[04_ESP32_Bridge_IoT]] #esp32
- [x] Carnet QR: Generación dinámica cifrada [[05_Frontend_Web_Portal]] #frontend
- [x] Deploy SSH: Script automatizado para Orange Pi [[07_Notas_de_Integracion]] #despliegue
- [x] Documentación: 10 archivos Obsidian verificados con código real [[00_MAPA_GENERAL_GTR]] #gtr

## 🔧 Mantenimiento

- [ ] Calibrar sensores ultrasónicos HC-SR04 periódicamente #hardware
- [ ] Rotar logs en Orange Pi (`get_logs.py`) #despliegue
- [ ] Verificar expiración de tokens JWT #backend
- [ ] Backup automatizado de PostgreSQL #despliegue

***

%% kanban:settings
```json
{
  "kanban-plugin": "basic",
  "show-relative-date": true
}
```
%%
