"""
Parking GTR — Reusable Widgets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Widgets reutilizables compartidos entre Admin Panel y Member Scanner.
"""

import customtkinter as ctk

from config.theme import GOLD, MUTED


class StatusLabel(ctk.CTkLabel):
    """Label de estado con método helper para cambiar texto y color."""

    def __init__(self, master, initial_text: str = "Estado: Conectando...", **kwargs):
        kwargs.setdefault("text_color", "gray")
        kwargs.setdefault("text", initial_text)
        super().__init__(master, **kwargs)

    def set_status(self, text: str, color: str = "gray") -> None:
        """Actualiza el texto y color del status."""
        self.configure(text=text, text_color=color)


class SidebarSection(ctk.CTkLabel):
    """Título de sección estilizado para barras laterales."""

    def __init__(self, master, text: str, **kwargs):
        kwargs.setdefault("font", ctk.CTkFont("Helvetica", 9, "bold"))
        kwargs.setdefault("text_color", GOLD)
        super().__init__(master, text=text, **kwargs)


class VehicleCard(ctk.CTkFrame):
    """Tarjeta de vehículo reutilizable.

    Muestra tipo de vehículo, servicio y estado con colores apropiados.
    """

    def __init__(
        self,
        master,
        vehicle_type: str,
        service: str,
        status: str,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", "#242424")
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#3a3a3a")
        super().__init__(master, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        # Tipo de vehículo
        ctk.CTkLabel(
            header,
            text=f"🚘 {vehicle_type.upper()}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        # Badge de estado
        color = "#2ecc71" if status == "completed" else "#f39c12"
        ctk.CTkLabel(
            header,
            text=status.upper(),
            text_color=color,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="right")

        # Info del servicio
        ctk.CTkLabel(
            self,
            text=f"Servicio Registrado: {service}",
            text_color="#b0b0b0",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=15, pady=(0, 10))


class StatsGrid(ctk.CTkFrame):
    """Grid de estadísticas con etiquetas doradas."""

    def __init__(self, master, stats: list[tuple[str, str]], **kwargs):
        """
        Args:
            stats: Lista de tuplas (label, value).
        """
        kwargs.setdefault("fg_color", "#2b2b2b")
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)

        for col, (label, value) in enumerate(stats):
            ctk.CTkLabel(
                self,
                text=f"{label}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=GOLD,
            ).grid(row=0, column=col, padx=10, pady=(10, 0), sticky="w")

            ctk.CTkLabel(
                self,
                text=value,
                font=ctk.CTkFont(size=14),
            ).grid(row=1, column=col, padx=10, pady=(0, 10), sticky="w")
