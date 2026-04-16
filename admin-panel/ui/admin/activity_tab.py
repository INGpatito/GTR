"""
Parking GTR — Activity Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tab de Registro de Actividad: muestra todas las reservaciones
en un Treeview con filtro de pendientes.
"""

import customtkinter as ctk
from tkinter import ttk

from config.theme import GOLD, apply_treeview_style


class ActivityTab:
    """Componente del tab 'Registro de Actividad'."""

    def __init__(self, parent_tab: ctk.CTkFrame, on_filter_change=None):
        """
        Args:
            parent_tab: Frame del tab donde se renderizan los widgets.
            on_filter_change: Callback cuando cambia el filtro de pendientes.
        """
        self.tab = parent_tab
        self.tab.grid_rowconfigure(1, weight=1)
        self.tab.grid_columnconfigure(0, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self.tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Registro de Actividad",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.filter_pending_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            header,
            text="🚨 Mostrar SÓLO Pendientes",
            variable=self.filter_pending_var,
            command=on_filter_change,
            fg_color=GOLD,
            hover_color="#b5952f",
        ).grid(row=0, column=2, sticky="e")

        # ── Aplicar estilos al Treeview ──
        apply_treeview_style()

        # ── Treeview ──
        columns = ("ID", "Nombre", "Servicio", "Vehículo", "Fecha y Hora", "Estado")
        self.tree = ttk.Treeview(self.tab, columns=columns, show="headings")

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Cliente")
        self.tree.heading("Servicio", text="Servicio")
        self.tree.heading("Vehículo", text="Vehículo")
        self.tree.heading("Fecha y Hora", text="Fecha de Llegada")
        self.tree.heading("Estado", text="Estado")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Nombre", width=150)
        self.tree.column("Servicio", width=120)
        self.tree.column("Vehículo", width=100)
        self.tree.column("Fecha y Hora", width=150)
        self.tree.column("Estado", width=100, anchor="center")

        self.tree.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    @property
    def is_pending_only(self) -> bool:
        """Retorna True si el filtro de pendientes está activo."""
        return self.filter_pending_var.get()

    def clear(self) -> None:
        """Elimina todas las filas del Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, values: tuple) -> None:
        """Inserta una fila en el Treeview."""
        self.tree.insert("", "end", values=values)

    def get_selected_values(self) -> tuple | None:
        """Retorna los valores de la fila seleccionada, o None."""
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0])["values"]
