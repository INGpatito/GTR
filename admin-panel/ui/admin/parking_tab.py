"""
Parking GTR — Parking Occupancy Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tab del panel de administración que muestra el estado de los 24
espacios de estacionamiento (3 pisos × 8 espacios) y el helipuerto.

Cada espacio muestra:
  - Etiqueta del espacio (P1-01, P2-03, etc.)
  - Estado (disponible / ocupado)
  - Si está ocupado: nombre del socio, vehículo (marca, modelo, placa)
    y cuánto tiempo lleva estacionado.
"""

import datetime

import customtkinter as ctk
from tkinter import ttk

from config.theme import (
    GOLD, GOLD_SOFT, MUTED, GREEN, GREEN_HOVER,
    RED, RED_HOVER, AMBER,
)


# ══════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════
FLOOR_LABELS = {1: "Piso 1", 2: "Piso 2", 3: "Piso 3"}
FLOOR_EMOJIS = {1: "🅿️", 2: "🅿️", 3: "🅿️"}
SPOT_STATUS_COLORS = {
    "available": ("#1a3a1a", GREEN, "LIBRE"),
    "occupied":  ("#3a1a1a", RED, "OCUPADO"),
}


def _format_elapsed(occupied_at) -> str:
    """Formatea el tiempo transcurrido desde occupied_at hasta ahora."""
    if not occupied_at:
        return ""
    try:
        if isinstance(occupied_at, str):
            occupied_at = datetime.datetime.fromisoformat(occupied_at)
        # Normalizar a naive UTC para comparación
        if occupied_at.tzinfo is not None:
            occupied_at = occupied_at.replace(tzinfo=None)
        delta = datetime.datetime.utcnow() - occupied_at
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            return "recién"
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return ""


# ══════════════════════════════════════════════════════
#  SPOT CARD (Widget individual por espacio)
# ══════════════════════════════════════════════════════
class SpotCard(ctk.CTkFrame):
    """Tarjeta visual para un espacio de estacionamiento."""

    def __init__(
        self,
        master,
        spot_label: str,
        status: str,
        user_name: str = "",
        vehicle_info: str = "",
        plate: str = "",
        elapsed: str = "",
        on_free=None,
        spot_id: int = None,
        **kwargs,
    ):
        is_occupied = status == "occupied"
        bg_color, accent, status_text = SPOT_STATUS_COLORS.get(
            status, SPOT_STATUS_COLORS["available"]
        )

        kwargs.setdefault("fg_color", bg_color)
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", accent if is_occupied else "#2a3a2a")
        super().__init__(master, **kwargs)

        # ── Header: Spot label + Status badge ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text=spot_label,
            font=ctk.CTkFont("Helvetica", 15, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"  {status_text}  ",
            font=ctk.CTkFont("Helvetica", 9, "bold"),
            text_color=accent,
            fg_color="#1a1a1a",
            corner_radius=4,
        ).pack(side="right")

        if is_occupied and user_name:
            # ── User info ──
            ctk.CTkLabel(
                self,
                text=f"👤  {user_name}",
                font=ctk.CTkFont("Helvetica", 12, "bold"),
                text_color=GOLD_SOFT,
                anchor="w",
            ).pack(anchor="w", padx=12, pady=(4, 0))

            # ── Vehicle info ──
            if vehicle_info:
                ctk.CTkLabel(
                    self,
                    text=f"🚗  {vehicle_info}",
                    font=ctk.CTkFont("Helvetica", 11),
                    text_color="#b0b0b0",
                    anchor="w",
                ).pack(anchor="w", padx=12, pady=(2, 0))

            # ── Plate + Elapsed row ──
            info_row = ctk.CTkFrame(self, fg_color="transparent")
            info_row.pack(fill="x", padx=12, pady=(4, 2))

            if plate:
                ctk.CTkLabel(
                    info_row,
                    text=f"  🪪 {plate}  ",
                    font=ctk.CTkFont("Helvetica", 9),
                    text_color=GOLD_SOFT,
                    fg_color="#2a2a1e",
                    corner_radius=4,
                ).pack(side="left", padx=(0, 6))

            if elapsed:
                ctk.CTkLabel(
                    info_row,
                    text=f"  ⏱ {elapsed}  ",
                    font=ctk.CTkFont("Helvetica", 9),
                    text_color=AMBER,
                    fg_color="#2a2a1e",
                    corner_radius=4,
                ).pack(side="left")

            # ── Free Spot Button ──
            if on_free and spot_id:
                ctk.CTkButton(
                    self,
                    text="🔓 Liberar Espacio",
                    font=ctk.CTkFont("Helvetica", 10, "bold"),
                    fg_color=RED,
                    hover_color=RED_HOVER,
                    height=28,
                    corner_radius=6,
                    command=lambda: on_free(spot_id, spot_label, user_name),
                ).pack(padx=12, pady=(6, 10))
            else:
                # Bottom padding
                ctk.CTkFrame(self, fg_color="transparent", height=6).pack()
        else:
            # ── Empty spot ──
            ctk.CTkLabel(
                self,
                text="Espacio disponible",
                font=ctk.CTkFont("Helvetica", 11),
                text_color="#4a6a4a",
                anchor="w",
            ).pack(anchor="w", padx=12, pady=(4, 10))


# ══════════════════════════════════════════════════════
#  FLOOR SECTION
# ══════════════════════════════════════════════════════
class FloorSection(ctk.CTkFrame):
    """Sección visual para un piso del estacionamiento."""

    def __init__(self, master, floor: int, spots: list, on_free=None, **kwargs):
        kwargs.setdefault("fg_color", "#1a1a1a")
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#2b2b2b")
        super().__init__(master, **kwargs)

        label = FLOOR_LABELS.get(floor, f"Piso {floor}")
        emoji = FLOOR_EMOJIS.get(floor, "🅿️")

        # Count occupied
        occupied = sum(1 for s in spots if s[4] == "occupied")
        total = len(spots)

        # ── Floor Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            header,
            text=f"{emoji}  {label}",
            font=ctk.CTkFont("Helvetica", 16, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        # Occupancy badge
        occ_color = RED if occupied == total else (AMBER if occupied > total // 2 else GREEN)
        ctk.CTkLabel(
            header,
            text=f"  {occupied}/{total} ocupados  ",
            font=ctk.CTkFont("Helvetica", 10, "bold"),
            text_color=occ_color,
            fg_color="#1a1a1a",
            corner_radius=6,
        ).pack(side="right")

        # ── Grid of spots (4 columns) ──
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=12, pady=(0, 14))

        for col in range(4):
            grid_frame.grid_columnconfigure(col, weight=1)

        for idx, spot in enumerate(spots):
            # spot = (id, spot_number, floor, spot_label, status,
            #         occupied_by_user_id, occupied_by_vehicle_id, occupied_at,
            #         user_name, vehicle_nickname, brand, model, plate)
            spot_id = spot[0]
            spot_label_text = spot[3] or f"P{spot[2]}-{spot[1]:02d}"
            status = spot[4] or "available"
            user_name = spot[8] or ""
            vehicle_nickname = spot[9] or ""
            brand = spot[10] or ""
            model = spot[11] or ""
            plate = spot[12] or ""
            occupied_at = spot[7]

            # Build vehicle description
            parts = [p for p in [brand, model] if p]
            vehicle_info = " ".join(parts) if parts else vehicle_nickname
            elapsed = _format_elapsed(occupied_at)

            row = idx // 4
            col = idx % 4

            card = SpotCard(
                grid_frame,
                spot_label=spot_label_text,
                status=status,
                user_name=user_name,
                vehicle_info=vehicle_info,
                plate=plate,
                elapsed=elapsed,
                on_free=on_free,
                spot_id=spot_id,
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")


# ══════════════════════════════════════════════════════
#  HELIPORT SECTION
# ══════════════════════════════════════════════════════
class HeliportSection(ctk.CTkFrame):
    """Sección visual para el helipuerto (floor=0)."""

    def __init__(self, master, heliport_data, on_free=None, **kwargs):
        kwargs.setdefault("fg_color", "#1a1a2a")
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#2b2b4b")
        super().__init__(master, **kwargs)

        # heliport_data = (id, spot_label, status, occupied_by_user_id, occupied_at, user_name)
        if not heliport_data:
            ctk.CTkLabel(
                self,
                text="🚁  Helipuerto no disponible",
                font=ctk.CTkFont("Helvetica", 14, "bold"),
                text_color=MUTED,
            ).pack(padx=16, pady=14)
            return

        spot_id = heliport_data[0]
        status = heliport_data[2] or "available"
        user_name = heliport_data[5] or ""
        occupied_at = heliport_data[4]
        is_occupied = status == "occupied"

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            header,
            text="🚁  Helipuerto",
            font=ctk.CTkFont("Helvetica", 16, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        status_color = RED if is_occupied else GREEN
        status_text = "OCUPADO" if is_occupied else "LIBRE"
        ctk.CTkLabel(
            header,
            text=f"  {status_text}  ",
            font=ctk.CTkFont("Helvetica", 10, "bold"),
            text_color=status_color,
            fg_color="#1a1a1a",
            corner_radius=6,
        ).pack(side="right")

        if is_occupied and user_name:
            ctk.CTkLabel(
                self,
                text=f"👤  {user_name}",
                font=ctk.CTkFont("Helvetica", 13, "bold"),
                text_color=GOLD_SOFT,
                anchor="w",
            ).pack(anchor="w", padx=18, pady=(2, 0))

            elapsed = _format_elapsed(occupied_at)
            if elapsed:
                ctk.CTkLabel(
                    self,
                    text=f"⏱  Tiempo estacionado: {elapsed}",
                    font=ctk.CTkFont("Helvetica", 11),
                    text_color=AMBER,
                    anchor="w",
                ).pack(anchor="w", padx=18, pady=(4, 4))

            if on_free:
                ctk.CTkButton(
                    self,
                    text="🔓 Liberar Helipuerto",
                    font=ctk.CTkFont("Helvetica", 10, "bold"),
                    fg_color=RED,
                    hover_color=RED_HOVER,
                    height=30,
                    corner_radius=6,
                    command=lambda: on_free(spot_id, "HELI-01", user_name),
                ).pack(padx=18, pady=(4, 14))
        else:
            ctk.CTkLabel(
                self,
                text="Helipuerto disponible",
                font=ctk.CTkFont("Helvetica", 11),
                text_color="#4a4a6a",
                anchor="w",
            ).pack(anchor="w", padx=18, pady=(2, 14))


# ══════════════════════════════════════════════════════
#  PARKING TAB (Tab principal)
# ══════════════════════════════════════════════════════
class ParkingTab:
    """Tab de ocupación de estacionamiento para el Admin Panel.

    Muestra una vista visual de los 24 spots + helipuerto,
    organizados por piso. Permite liberar espacios ocupados.
    """

    def __init__(self, parent_frame, on_free_spot=None):
        """
        Args:
            parent_frame: Frame del tab contenedor.
            on_free_spot: Callback(spot_id, spot_label, user_name) para liberar un espacio.
        """
        self.parent = parent_frame
        self.on_free_spot = on_free_spot
        self._floor_sections = []

        # ── Main scrollable frame ──
        self.scroll_frame = ctk.CTkScrollableFrame(
            parent_frame,
            fg_color="transparent",
            scrollbar_button_color="#2b2b2b",
            scrollbar_button_hover_color="#3b3b3b",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # ── Summary bar ──
        self.summary_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="#1e1e2e",
            corner_radius=12,
            border_width=1,
            border_color="#2b2b3b",
        )
        self.summary_frame.pack(fill="x", padx=4, pady=(4, 8))

        self.summary_label = ctk.CTkLabel(
            self.summary_frame,
            text="Cargando datos de estacionamiento...",
            font=ctk.CTkFont("Helvetica", 12),
            text_color=MUTED,
        )
        self.summary_label.pack(padx=16, pady=10)

        # ── Content area ──
        self.content_frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True)

    def clear(self) -> None:
        """Limpia todo el contenido del tab."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self._floor_sections.clear()

    def populate(self, all_spots: list, heliport_data=None) -> None:
        """Llena el tab con los datos de spots.

        Args:
            all_spots: Lista de tuplas como las retornadas por parking_service.get_all_spots().
            heliport_data: Tupla del helipuerto como retornada por parking_service.get_heliport_status().
        """
        self.clear()

        # ── Summary stats ──
        total = len(all_spots)
        occupied = sum(1 for s in all_spots if s[4] == "occupied")
        available = total - occupied
        heli_occupied = heliport_data and heliport_data[2] == "occupied" if heliport_data else False

        occ_pct = (occupied / total * 100) if total > 0 else 0
        summary_color = RED if occ_pct > 80 else (AMBER if occ_pct > 50 else GREEN)

        self.summary_label.configure(
            text=(
                f"📊  Total: {total} espacios  ·  "
                f"🔴 Ocupados: {occupied}  ·  "
                f"🟢 Libres: {available}  ·  "
                f"Ocupación: {occ_pct:.0f}%  ·  "
                f"🚁 Helipuerto: {'OCUPADO' if heli_occupied else 'LIBRE'}"
            ),
            text_color=summary_color,
        )

        # ── Group by floor ──
        floors = {}
        for spot in all_spots:
            floor = spot[2]
            floors.setdefault(floor, []).append(spot)

        # ── Render each floor ──
        for floor_num in sorted(floors.keys()):
            if floor_num == 0:
                continue  # Skip heliport in main floor loop
            section = FloorSection(
                self.content_frame,
                floor=floor_num,
                spots=floors[floor_num],
                on_free=self.on_free_spot,
            )
            section.pack(fill="x", padx=4, pady=(0, 8))
            self._floor_sections.append(section)

        # ── Heliport ──
        heli_section = HeliportSection(
            self.content_frame,
            heliport_data=heliport_data,
            on_free=self.on_free_spot,
        )
        heli_section.pack(fill="x", padx=4, pady=(0, 8))
        self._floor_sections.append(heli_section)
