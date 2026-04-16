"""
Parking GTR — Admin Sidebar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Barra lateral del panel de administración con botones de acción
y toggle de auto-refresh.
"""

import customtkinter as ctk

from config.theme import GREEN, GREEN_HOVER, RED, RED_HOVER
from ui.widgets import StatusLabel


class AdminSidebar(ctk.CTkFrame):
    """Sidebar del Admin Panel con botones y estado."""

    def __init__(self, master, callbacks: dict, **kwargs):
        """
        Args:
            callbacks: Dict con claves 'refresh', 'complete', 'delete'.
                       Cada valor es un callable.
        """
        kwargs.setdefault("width", 200)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.grid_rowconfigure(4, weight=1)

        self._auto_refresh = False
        self._auto_refresh_id = None
        self._on_refresh = callbacks.get("refresh", lambda: None)

        # ── Logo ──
        ctk.CTkLabel(
            self,
            text="Parking GTR",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # ── Botón: Actualizar ──
        ctk.CTkButton(
            self,
            text="⟳ Actualizar Datos",
            command=self._on_refresh,
        ).grid(row=1, column=0, padx=20, pady=10)

        # ── Botón: Completar ──
        ctk.CTkButton(
            self,
            text="✅ Marcar Completado",
            fg_color=GREEN,
            hover_color=GREEN_HOVER,
            command=callbacks.get("complete", lambda: None),
        ).grid(row=2, column=0, padx=20, pady=10)

        # ── Botón: Eliminar ──
        ctk.CTkButton(
            self,
            text="🗑 Eliminar Registro",
            fg_color=RED,
            hover_color=RED_HOVER,
            command=callbacks.get("delete", lambda: None),
        ).grid(row=3, column=0, padx=20, pady=10)

        # ── Toggle Auto Refresh ──
        self.btn_auto = ctk.CTkButton(
            self,
            text="🔄 Auto-Refresh: OFF",
            fg_color="#555555",
            hover_color="#666666",
            command=self._toggle_auto_refresh,
        )
        self.btn_auto.grid(row=4, column=0, padx=20, pady=10)

        # ── Status Label ──
        self.status = StatusLabel(self, initial_text="Estado: Conectando...")
        self.status.grid(row=6, column=0, padx=20, pady=20, sticky="s")

    # ──────────────────────────────────────────────────
    #  AUTO REFRESH
    # ──────────────────────────────────────────────────
    def _toggle_auto_refresh(self) -> None:
        self._auto_refresh = not self._auto_refresh
        if self._auto_refresh:
            self.btn_auto.configure(
                text="🔄 Auto-Refresh: ON",
                fg_color="#1f538d",
                hover_color="#1a4570",
            )
            self._auto_refresh_tick()
        else:
            self.btn_auto.configure(
                text="🔄 Auto-Refresh: OFF",
                fg_color="#555555",
                hover_color="#666666",
            )
            if self._auto_refresh_id:
                self.after_cancel(self._auto_refresh_id)
                self._auto_refresh_id = None

    def _auto_refresh_tick(self) -> None:
        if not self._auto_refresh:
            return
        self._on_refresh()
        self._auto_refresh_id = self.after(30000, self._auto_refresh_tick)

    def cleanup(self) -> None:
        """Cancela el auto-refresh timer si está activo."""
        if self._auto_refresh_id:
            self.after_cancel(self._auto_refresh_id)
            self._auto_refresh_id = None
