"""
Parking GTR — Scanner Sidebar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Barra lateral del Member Scanner con búsqueda por tarjeta,
búsqueda por ID admin, y stub de sensores.
"""

import customtkinter as ctk

from config.theme import GOLD, MUTED
from ui.widgets import SidebarSection, StatusLabel


class ScannerSidebar(ctk.CTkFrame):
    """Sidebar del Member Scanner con controles de búsqueda."""

    def __init__(self, master, callbacks: dict, **kwargs):
        """
        Args:
            callbacks: Dict con claves:
                - 'search_card': Callable(card_number: str)
                - 'search_id': Callable(member_id: str)
                - 'simulate': Callable()
        """
        from config.theme import CARD_BG
        kwargs.setdefault("width", 260)
        kwargs.setdefault("fg_color", CARD_BG)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.grid_propagate(False)
        self.grid_rowconfigure(99, weight=1)

        self._on_search_card = callbacks.get("search_card", lambda v: None)
        self._on_search_id = callbacks.get("search_id", lambda v: None)

        # ── Logo ──
        ctk.CTkLabel(
            self,
            text="▲ GTR",
            font=ctk.CTkFont("Helvetica", 28, "bold"),
            text_color=GOLD,
        ).grid(row=0, column=0, padx=24, pady=(28, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text="MEMBER SCANNER",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=MUTED,
        ).grid(row=1, column=0, padx=26, pady=(0, 24), sticky="w")

        # ── Sección: Número de Tarjeta ──
        SidebarSection(self, text="NÚMERO DE TARJETA").grid(
            row=2, column=0, padx=20, pady=(8, 0), sticky="w"
        )

        self.card_entry = ctk.CTkEntry(
            self,
            placeholder_text="3153 7028 2894 1005",
            font=ctk.CTkFont("Courier", 13),
            height=40,
            corner_radius=8,
            border_color=GOLD,
            border_width=1,
        )
        self.card_entry.grid(row=3, column=0, padx=16, pady=(4, 8), sticky="ew")
        self.card_entry.bind("<Return>", lambda e: self._on_card_submit())

        ctk.CTkButton(
            self,
            text="🔍  Verificar Tarjeta",
            height=38,
            corner_radius=8,
            fg_color=GOLD,
            text_color="#000",
            hover_color="#b5952f",
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._on_card_submit,
        ).grid(row=4, column=0, padx=16, pady=(0, 24), sticky="ew")

        # ── Sección: Admin — Buscar por ID ──
        SidebarSection(self, text="ADMIN — BUSCAR POR ID").grid(
            row=5, column=0, padx=20, pady=(8, 0), sticky="w"
        )

        self.id_entry = ctk.CTkEntry(
            self,
            placeholder_text="ID interno  (ej: 23)",
            font=ctk.CTkFont("Helvetica", 12),
            height=36,
            corner_radius=8,
            border_color="#3a3a3a",
            border_width=1,
            text_color="#888",
        )
        self.id_entry.grid(row=6, column=0, padx=16, pady=(4, 8), sticky="ew")
        self.id_entry.bind("<Return>", lambda e: self._on_id_submit())

        ctk.CTkButton(
            self,
            text="⚙️  Buscar (Admin)",
            height=34,
            corner_radius=8,
            fg_color="#252525",
            text_color="#666",
            hover_color="#333",
            border_color="#333",
            border_width=1,
            font=ctk.CTkFont("Helvetica", 11),
            command=self._on_id_submit,
        ).grid(row=7, column=0, padx=16, pady=(0, 24), sticky="ew")

        # ── Sección: Sensores (stub) ──
        SidebarSection(self, text="SENSORES (PRÓXIMAMENTE)").grid(
            row=8, column=0, padx=20, pady=(8, 0), sticky="w"
        )

        sensor_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=8)
        sensor_frame.grid(row=9, column=0, padx=16, pady=(4, 24), sticky="ew")

        ctk.CTkLabel(
            sensor_frame,
            text="🔌  Sin sensor conectado",
            font=ctk.CTkFont("Helvetica", 11),
            text_color=MUTED,
        ).pack(padx=12, pady=10)

        ctk.CTkButton(
            sensor_frame,
            text="▶ Simular Lectura",
            height=30,
            corner_radius=6,
            fg_color="#2b2b2b",
            text_color="#888",
            hover_color="#333",
            font=ctk.CTkFont("Helvetica", 11),
            command=callbacks.get("simulate", lambda: None),
        ).pack(padx=12, pady=(0, 10), fill="x")

        # ── Estado DB ──
        self.db_status = StatusLabel(
            self,
            initial_text="● Sin conexión",
            font=ctk.CTkFont("Helvetica", 10),
        )
        self.db_status.grid(row=99, column=0, padx=16, pady=16, sticky="sw")

    def _on_card_submit(self) -> None:
        value = self.card_entry.get().strip()
        self._on_search_card(value)

    def _on_id_submit(self) -> None:
        value = self.id_entry.get().strip()
        self._on_search_id(value)
