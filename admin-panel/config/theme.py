"""
Parking GTR — Theme & Style Constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Paleta de colores, fuentes y estilos de Treeview compartidos
por ambas aplicaciones (Admin Panel y Member Scanner).
"""

import customtkinter as ctk
from tkinter import ttk

# ══════════════════════════════════════════════════════
#  PALETA DE COLORES
# ══════════════════════════════════════════════════════
GOLD        = "#d4af37"
GOLD_SOFT   = "#c8bc98"
DARK_BG     = "#0d0d0d"
CARD_BG     = "#161616"
PANEL_BG    = "#1e1e1e"
MUTED       = "#666666"
GREEN       = "#2ecc71"
GREEN_HOVER = "#27ae60"
RED         = "#e74c3c"
RED_HOVER   = "#c0392b"
AMBER       = "#f39c12"
SIDEBAR_BG  = "#1a1a1a"

# ══════════════════════════════════════════════════════
#  EMOJIS POR TIPO DE VEHÍCULO / SERVICIO
# ══════════════════════════════════════════════════════
VEHICLE_EMOJI: dict[str, str] = {
    "sports":      "🏎",
    "suv":         "🚙",
    "sedan":       "🚗",
    "convertible": "🚘",
    "exotic":      "🏆",
}

TIER_EMOJI: dict[str, str] = {
    "valet":     "🤵",
    "monthly":   "📅",
    "concierge": "⭐",
    "fleet":     "🏢",
    "event":     "🎭",
}


# ══════════════════════════════════════════════════════
#  CONFIGURACIÓN DE TEMA CTK
# ══════════════════════════════════════════════════════
def setup_ctk_theme() -> None:
    """Aplica la configuración global de customtkinter."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def apply_treeview_style() -> None:
    """Aplica el estilo oscuro-dorado a los widgets ttk.Treeview."""
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background="#1a1a1a",
        foreground="#e0e0e0",
        rowheight=35,
        fieldbackground="#1a1a1a",
        bordercolor="#2b2b2b",
        borderwidth=0,
        font=("Helvetica", 10),
    )
    style.map(
        "Treeview",
        background=[("selected", GOLD)],
        foreground=[("selected", "#000000")],
    )
    style.configure(
        "Treeview.Heading",
        background="#2a2a2a",
        foreground=GOLD,
        relief="flat",
        font=("Helvetica", 10, "bold"),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#3a3a3a")],
    )
