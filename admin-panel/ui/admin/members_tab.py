"""
Parking GTR — Members Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tab de Directorio de Socios: Treeview con el listado de miembros
y panel lateral de detalles con historial de vehículos.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox

from config.theme import GOLD, RED, RED_HOVER
from ui.widgets import StatsGrid, VehicleCard


class MembersTab:
    """Componente del tab 'Directorio de Socios'."""

    def __init__(
        self,
        parent_tab: ctk.CTkFrame,
        on_select_member=None,
        on_delete_member=None,
        on_security=None,
    ):
        """
        Args:
            parent_tab: Frame del tab donde se renderizan los widgets.
            on_select_member: Callback(email) cuando se selecciona un socio.
            on_delete_member: Callback() al presionar eliminar socio.
            on_security: Callback(email) al presionar seguridad.
        """
        self.tab = parent_tab
        self._on_security = on_security
        self.tab.grid_rowconfigure(1, weight=1)
        self.tab.grid_columnconfigure(0, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self.tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Directorio de Socios",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="🗑 Eliminar Socio",
            fg_color=RED,
            hover_color=RED_HOVER,
            width=140,
            command=on_delete_member,
        ).grid(row=0, column=1, sticky="e")

        # ── Split layout ──
        split = ctk.CTkFrame(self.tab, fg_color="transparent")
        split.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        split.grid_rowconfigure(0, weight=1)
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=2)

        # ── Treeview ──
        columns = ("Email", "Nombre", "Vehículos", "Suscripción Mayor")
        self.tree = ttk.Treeview(split, columns=columns, show="headings")

        self.tree.heading("Email", text="Email (Cuenta)")
        self.tree.heading("Nombre", text="Último Nombre")
        self.tree.heading("Vehículos", text="Total Vehículos")
        self.tree.heading("Suscripción Mayor", text="Suscripción")

        self.tree.column("Email", width=180)
        self.tree.column("Nombre", width=150)
        self.tree.column("Vehículos", width=80, anchor="center")
        self.tree.column("Suscripción Mayor", width=120)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select(on_select_member))

        # ── Panel de Detalles ──
        self.detail_frame = ctk.CTkScrollableFrame(
            split, corner_radius=10, fg_color="#1e1e1e"
        )
        self.detail_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.show_empty_details()

    # ──────────────────────────────────────────────────
    #  TREEVIEW OPERATIONS
    # ──────────────────────────────────────────────────
    def clear(self) -> None:
        """Elimina todas las filas del Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, values: tuple) -> None:
        """Inserta una fila en el Treeview."""
        self.tree.insert("", "end", values=values)

    def get_selected_email(self) -> str | None:
        """Retorna el email del socio seleccionado, o None."""
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0])["values"][0]

    def _on_select(self, callback) -> None:
        email = self.get_selected_email()
        if email and callback:
            callback(email)

    # ──────────────────────────────────────────────────
    #  DETAIL PANEL
    # ──────────────────────────────────────────────────
    def show_empty_details(self) -> None:
        """Muestra el estado vacío del panel de detalles."""
        self._clear_details()

        ctk.CTkLabel(
            self.detail_frame,
            text="👤",
            font=ctk.CTkFont(size=40),
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            self.detail_frame,
            text="Selecciona un socio\nen la tabla para ver\nsu información.",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack()

    def show_member_details(
        self,
        email: str,
        nombre: str,
        telefono: str,
        sub_nivel: str,
        total_coches: int,
        historial: list[tuple],
    ) -> None:
        """Renderiza los detalles completos de un socio en el panel lateral."""
        self._clear_details()

        # ── Header del Socio ──
        hdr = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 20), padx=10)
        hdr.grid_columnconfigure(0, weight=1)

        info_f = ctk.CTkFrame(hdr, fg_color="transparent")
        info_f.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            info_f,
            text=nombre,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=GOLD,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_f,
            text=email,
            font=ctk.CTkFont(size=13),
            text_color="#a0a0a0",
        ).pack(anchor="w")

        if self._on_security:
            ctk.CTkButton(
                hdr,
                text="🔒 Seguridad",
                width=100,
                fg_color="#c0392b",
                hover_color="#922b21",
                command=lambda: self._on_security(email),
            ).grid(row=0, column=1, sticky="e")

        # ── Stats Grid ──
        stats = StatsGrid(
            self.detail_frame,
            stats=[
                ("Suscripción", sub_nivel),
                ("Teléfono", telefono),
                ("Vehículos", str(total_coches)),
            ],
        )
        stats.pack(fill="x", padx=10, pady=(0, 20))

        # ── Historial de Vehículos ──
        ctk.CTkLabel(
            self.detail_frame,
            text="Historial de Vehículos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(0, 10))

        for record in historial:
            v_type = record[3].upper() if record[3] else "DESCONOCIDO"
            v_status = record[4] if record[4] else "pending"
            v_service = record[2] if record[2] else "N/A"

            VehicleCard(
                self.detail_frame,
                vehicle_type=v_type,
                service=v_service,
                status=v_status,
            ).pack(fill="x", padx=10, pady=5)

    def _clear_details(self) -> None:
        """Limpia todos los widgets del panel de detalles."""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
