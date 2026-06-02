"""
Parking GTR — Reusable Widgets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Widgets reutilizables compartidos entre Admin Panel y Member Scanner.
Alineados con la BD actual y GTR-Profile.
"""

import customtkinter as ctk

from config.theme import GOLD, GOLD_SOFT, MUTED, GREEN, AMBER, RED


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


class MembershipBadge(ctk.CTkFrame):
    """Badge de membresía coloreado por tier."""

    TIER_COLORS = {
        "none":     ("#555555", "#aaaaaa", "MEMBER"),
        "silver":   ("#6b7b8d", "#c0c8d0", "SILVER"),
        "gold":     ("#8b6914", "#d4af37", "GOLD PRESTIGE"),
        "platinum": ("#4a5568", "#a0aec0", "PLATINUM ELITE"),
    }

    def __init__(self, master, tier: str = "none", **kwargs):
        colors = self.TIER_COLORS.get(tier, self.TIER_COLORS["none"])
        kwargs.setdefault("fg_color", colors[0])
        kwargs.setdefault("corner_radius", 6)
        super().__init__(master, **kwargs)

        ctk.CTkLabel(
            self,
            text=f"  {colors[2]}  ",
            font=ctk.CTkFont("Helvetica", 10, "bold"),
            text_color=colors[1],
        ).pack(padx=4, pady=2)


class VehicleCard(ctk.CTkFrame):
    """Tarjeta de vehículo completa, alineada con user_vehicles.

    Muestra nickname, tipo, marca/modelo/año, color, placa y badge primario.
    """

    VEHICLE_EMOJI = {
        "sports":      "🏎",
        "suv":         "🚙",
        "sedan":       "🚗",
        "convertible": "🚘",
        "exotic":      "🏆",
    }

    def __init__(
        self,
        master,
        nickname: str = "Vehicle",
        vehicle_type: str = "sports",
        brand: str = "",
        model: str = "",
        year: int | None = None,
        color: str = "",
        plate: str = "",
        is_primary: bool = False,
        # Legacy params (backward compat)
        service: str = "",
        status: str = "",
        **kwargs,
    ):
        border_color = GOLD if is_primary else "#3a3a3a"
        kwargs.setdefault("fg_color", "#242424")
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", border_color)
        super().__init__(master, **kwargs)

        emoji = self.VEHICLE_EMOJI.get(vehicle_type, "🚗")

        # ── Header Row ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text=f"{emoji}  {nickname}",
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            anchor="w",
        ).pack(side="left")

        if is_primary:
            ctk.CTkLabel(
                header,
                text="  ★ Principal  ",
                font=ctk.CTkFont("Helvetica", 9, "bold"),
                text_color="#000",
                fg_color=GOLD,
                corner_radius=4,
            ).pack(side="right")

        # ── Meta info ──
        meta_parts = [p for p in [brand, model, str(year) if year else None] if p]
        meta_text = " · ".join(meta_parts) if meta_parts else (vehicle_type or "").title()

        ctk.CTkLabel(
            self,
            text=meta_text,
            font=ctk.CTkFont("Helvetica", 11),
            text_color=MUTED,
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(0, 2))

        # ── Tags row ──
        tags_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_frame.pack(fill="x", padx=12, pady=(0, 10))

        if vehicle_type:
            ctk.CTkLabel(
                tags_frame,
                text=f"  {vehicle_type.upper()}  ",
                font=ctk.CTkFont("Helvetica", 9),
                text_color="#999",
                fg_color="#333",
                corner_radius=4,
            ).pack(side="left", padx=(0, 4))

        if plate:
            ctk.CTkLabel(
                tags_frame,
                text=f"  🪪 {plate}  ",
                font=ctk.CTkFont("Helvetica", 9),
                text_color=GOLD_SOFT,
                fg_color="#2a2a1e",
                corner_radius=4,
            ).pack(side="left", padx=(0, 4))

        if color:
            ctk.CTkLabel(
                tags_frame,
                text=f"  {color}  ",
                font=ctk.CTkFont("Helvetica", 9),
                text_color="#aaa",
                fg_color="#333",
                corner_radius=4,
            ).pack(side="left", padx=(0, 4))

        # Legacy compat: si se pasan service/status en modo antiguo
        if service and not nickname:
            ctk.CTkLabel(
                self,
                text=f"Servicio: {service}",
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

        # Hasta 3 columnas, el resto salta a segunda fila
        cols = min(len(stats), 3)
        for c in range(cols):
            self.grid_columnconfigure(c, weight=1)

        for idx, (label, value) in enumerate(stats):
            row = idx // 3
            col = idx % 3

            ctk.CTkLabel(
                self,
                text=f"{label}",
                font=ctk.CTkFont("Helvetica", 10),
                text_color=MUTED,
            ).grid(row=row * 2, column=col, padx=10, pady=(10, 0), sticky="w")

            ctk.CTkLabel(
                self,
                text=value,
                font=ctk.CTkFont("Helvetica", 13, "bold"),
                text_color=GOLD_SOFT,
            ).grid(row=row * 2 + 1, column=col, padx=10, pady=(0, 10), sticky="w")
