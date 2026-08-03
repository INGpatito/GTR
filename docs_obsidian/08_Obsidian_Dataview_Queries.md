---
tags: [gtr, obsidian, dataview, consultas]
aliases: [Queries GTR, Consultas Dataview]
---

# 📊 Consultas Dataview

> **TL;DR** — Queries pre-armadas para Obsidian Dataview. Copiar y pegar en cualquier nota.

⬅️ [[07_Notas_de_Integracion]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[09_Kanban_Estado_Proyecto]] ➡️

> [!note] Requiere el plugin **Dataview** instalado en Obsidian.

---

## 📋 Índice General (todas las notas GTR)

```dataview
TABLE status AS "Estado", progreso AS "Progreso", aliases AS "Alias"
FROM #gtr
SORT file.name ASC
```

---

## 🖥️ Módulos Backend & API

```dataview
TABLE status AS "Estado", progreso AS "%"
FROM #backend OR #api
SORT file.name ASC
```

---

## 📡 Hardware & IoT

```dataview
TABLE status AS "Estado", progreso AS "%"
FROM #esp32 OR #hardware OR #iot
SORT file.name ASC
```

---

## 🌐 Interfaces (Web + Mobile)

```dataview
TABLE status AS "Estado", progreso AS "%"
FROM #frontend OR #android OR #web OR #mobile
SORT file.name ASC
```

---

## 🔄 Integración & Deploy

```dataview
TABLE status AS "Estado", progreso AS "%"
FROM #despliegue OR #integración
SORT file.name ASC
```

---

## ⚡ Matriz Interactiva (DataviewJS)

```dataviewjs
dv.header(3, "🧩 Componentes GTR");
let pages = dv.pages('#gtr').where(p => p.progreso);
dv.table(
  ["Nota", "Estado", "Progreso"],
  pages.map(p => [p.file.link, p.status || "—", (p.progreso || 0) + "%"])
);
```

---

⬅️ [[07_Notas_de_Integracion]] · [[00_MAPA_GENERAL_GTR|🗺️ Mapa]] · [[09_Kanban_Estado_Proyecto]] ➡️
