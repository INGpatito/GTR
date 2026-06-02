"""
Parking GTR — Members Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tab de Directorio de Socios: Treeview con el listado de miembros
y panel lateral de detalles con garaje, membresía y actividad.

Alineado con la BD actual (users, user_vehicles, reservations)
y con la estructura de GTR-Profile.
"""

import datetime

import customtkinter as ctk
from tkinter import ttk, messagebox

from config.theme import GOLD, GOLD_SOFT, MUTED, GREEN, AMBER, RED, RED_HOVER
from ui.widgets import StatsGrid, VehicleCard, MembershipBadge


# ── Mapeos visuales (mismos que GTR-Profile) ──────────
TIER_LABELS = {
    "none":     "MEMBER",
    "silver":   "SILVER",
    "gold":     "GOLD PRESTIGE",
    "platinum": "PLATINUM ELITE",
}

TIER_COLORS = {
    "none":     MUTED,
    "silver":   "#c0c8d0",
    "gold":     GOLD,
    "platinum": "#a0aec0",
}

STATUS_COLORS = {
    "active":    GREEN,
    "confirmed": GREEN,
    "completed": GREEN,
    "pending":   AMBER,
}

SERVICE_LABELS = {
    "valet":     "VALET",
    "monthly":   "MONTHLY",
    "concierge": "CONCIERGE",
    "fleet":     "FLEET",
    "event":     "VIP PASS",
}


class MembersTab:
    """Componente del tab 'Directorio de Socios'."""

    def __init__(
        self,
        parent_tab: ctk.CTkFrame,
        on_select_member=None,
        on_delete_member=None,
        on_security=None,
        on_change_membership=None,
    ):
        """
        Args:
            parent_tab: Frame del tab donde se renderizan los widgets.
            on_select_member: Callback(user_id) cuando se selecciona un socio.
            on_delete_member: Callback() al presionar eliminar socio.
            on_security: Callback(email) al presionar seguridad.
            on_change_membership: Callback(user_id, tier) al cambiar membresía.
        """
        self.tab = parent_tab
        self._on_security = on_security
        self._on_change_membership = on_change_membership
        self._current_user_id = None
        self._current_email = None

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
        columns = ("ID", "Nombre", "Email", "Membresía", "Vehículos", "Estado")
        self.tree = ttk.Treeview(split, columns=columns, show="headings")

        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Membresía", text="Membresía")
        self.tree.heading("Vehículos", text="Vehículos")
        self.tree.heading("Estado", text="Estado")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nombre", width=140)
        self.tree.column("Email", width=180)
        self.tree.column("Membresía", width=100, anchor="center")
        self.tree.column("Vehículos", width=70, anchor="center")
        self.tree.column("Estado", width=80, anchor="center")

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
        """Inserta una fila en el Treeview.
        
        Espera: (id, full_name, email, membership_tier, vehicle_count, status)
        """
        self.tree.insert("", "end", values=values)

    def get_selected_user_id(self) -> int | None:
        """Retorna el ID del socio seleccionado, o None."""
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0])["values"]
        return int(values[0]) if values else None

    def get_selected_email(self) -> str | None:
        """Retorna el email del socio seleccionado, o None."""
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0])["values"]
        return str(values[2]) if values and len(values) > 2 else None

    def _on_select(self, callback) -> None:
        user_id = self.get_selected_user_id()
        if user_id and callback:
            callback(user_id)

    # ──────────────────────────────────────────────────
    #  DETAIL PANEL — Empty State
    # ──────────────────────────────────────────────────
    def show_empty_details(self) -> None:
        """Muestra el estado vacío del panel de detalles."""
        self._clear_details()

        ctk.CTkLabel(
            self.detail_frame,
            text="◆",
            font=ctk.CTkFont(size=48),
            text_color=GOLD,
        ).pack(pady=(60, 8))

        ctk.CTkLabel(
            self.detail_frame,
            text="PARKING GTR",
            font=ctk.CTkFont("Helvetica", 18, "bold"),
            text_color=GOLD,
        ).pack()

        ctk.CTkLabel(
            self.detail_frame,
            text="Selecciona un socio\nen la tabla para ver\nsu perfil completo.",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            justify="center",
        ).pack(pady=(12, 0))

    # ──────────────────────────────────────────────────
    #  DETAIL PANEL — Full Profile
    # ──────────────────────────────────────────────────
    def show_member_details(
        self,
        user_id: int,
        nombre: str,
        email: str,
        telefono: str,
        membership_tier: str,
        preferred_service: str,
        status: str,
        created_at,
        card_number: str,
        vehicles: list[tuple],
        activity: list[tuple],
    ) -> None:
        """Renderiza los detalles completos de un socio en el panel lateral.
        
        Alineado con GTR-Profile: muestra VIP Card info, stats, garaje y actividad.
        """
        self._clear_details()
        self._current_user_id = user_id
        self._current_email = email

        tier = membership_tier or "none"
        tier_label = TIER_LABELS.get(tier, "MEMBER")
        tier_color = TIER_COLORS.get(tier, MUTED)
        status_color = STATUS_COLORS.get(status, MUTED)

        # ── 1. HEADER: Nombre + Tier Badge ──────────────
        hdr = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 6), padx=10)
        hdr.grid_columnconfigure(0, weight=1)

        info_f = ctk.CTkFrame(hdr, fg_color="transparent")
        info_f.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            info_f,
            text=nombre,
            font=ctk.CTkFont("Helvetica", 20, "bold"),
            text_color=GOLD,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_f,
            text=email,
            font=ctk.CTkFont("Helvetica", 11),
            text_color="#a0a0a0",
        ).pack(anchor="w")

        # Tier badge + status
        badge_row = ctk.CTkFrame(info_f, fg_color="transparent")
        badge_row.pack(anchor="w", pady=(4, 0))

        MembershipBadge(badge_row, tier=tier).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            badge_row,
            text=f"  {status.upper()}  ",
            font=ctk.CTkFont("Helvetica", 9, "bold"),
            text_color="#000",
            fg_color=status_color,
            corner_radius=4,
        ).pack(side="left")

        # Security button
        if self._on_security:
            ctk.CTkButton(
                hdr,
                text="🔒",
                width=36, height=36,
                fg_color="#c0392b",
                hover_color="#922b21",
                corner_radius=8,
                command=lambda: self._on_security(email),
            ).grid(row=0, column=1, sticky="ne")

        # ── 2. STATS GRID ──────────────────────────────
        padded_id = f"GTR-{str(user_id).zfill(4)}"
        member_since = ""
        days_member = 0
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.datetime.fromisoformat(created_at)
            member_since = created_at.strftime("%d %b %Y")
            days_member = (datetime.datetime.now(tz=created_at.tzinfo) - created_at).days

        stats = StatsGrid(
            self.detail_frame,
            stats=[
                ("ID Socio", padded_id),
                ("Membresía", tier_label),
                ("Servicio", (preferred_service or "valet").upper()),
                ("Vehículos", f"{len(vehicles)}"),
                ("Días Socio", str(days_member)),
                ("Teléfono", telefono or "—"),
            ],
        )
        stats.pack(fill="x", padx=10, pady=(6, 10))

        # ── Card Number ──────────────────────────────
        card_frame = ctk.CTkFrame(self.detail_frame, fg_color="#1a1a1a", corner_radius=8)
        card_frame.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            card_frame,
            text="TARJETA GTR",
            font=ctk.CTkFont("Helvetica", 9),
            text_color=MUTED,
        ).pack(anchor="w", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            card_frame,
            text=card_number,
            font=ctk.CTkFont("Courier", 16, "bold"),
            text_color="#e0e0e0",
        ).pack(anchor="w", padx=12, pady=(2, 8))

        # ── 3. GARAJE ─────────────────────────────────
        ctk.CTkLabel(
            self.detail_frame,
            text="🚗  Garaje del Socio",
            font=ctk.CTkFont("Helvetica", 14, "bold"),
            text_color=GOLD,
        ).pack(anchor="w", padx=10, pady=(8, 6))

        if not vehicles:
            ctk.CTkLabel(
                self.detail_frame,
                text="Sin vehículos registrados.",
                text_color=MUTED,
                font=ctk.CTkFont("Helvetica", 11),
            ).pack(padx=14, pady=(0, 8))
        else:
            for v in vehicles:
                # (id, nickname, vehicle, brand, model, year, color, plate, is_primary)
                VehicleCard(
                    self.detail_frame,
                    nickname=v[1] or "Vehicle",
                    vehicle_type=v[2] or "sports",
                    brand=v[3] or "",
                    model=v[4] or "",
                    year=v[5],
                    color=v[6] or "",
                    plate=v[7] or "",
                    is_primary=bool(v[8]),
                ).pack(fill="x", padx=10, pady=3)

        # ── 4. ACTIVIDAD RECIENTE ─────────────────────
        ctk.CTkLabel(
            self.detail_frame,
            text="📋  Actividad Reciente",
            font=ctk.CTkFont("Helvetica", 14, "bold"),
            text_color=GOLD,
        ).pack(anchor="w", padx=10, pady=(14, 6))

        if not activity:
            ctk.CTkLabel(
                self.detail_frame,
                text="Sin actividad registrada.",
                text_color=MUTED,
                font=ctk.CTkFont("Helvetica", 11),
            ).pack(padx=14, pady=(0, 8))
        else:
            for act in activity:
                # (id, service, vehicle, status, created_at)
                a_svc = SERVICE_LABELS.get(act[1], (act[1] or "RESERVACIÓN").upper())
                a_status = act[3] or "pending"
                a_color = STATUS_COLORS.get(a_status, MUTED)
                a_date = ""
                if act[4]:
                    a_date = act[4].strftime("%d %b %Y") if hasattr(act[4], 'strftime') else str(act[4])

                af = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
                af.pack(fill="x", padx=14, pady=2)

                ctk.CTkLabel(
                    af, text="◆",
                    font=ctk.CTkFont("Helvetica", 8),
                    text_color=a_color,
                ).pack(side="left", padx=(0, 6))

                ctk.CTkLabel(
                    af, text=a_svc,
                    font=ctk.CTkFont("Helvetica", 11),
                    anchor="w",
                ).pack(side="left")

                ctk.CTkLabel(
                    af, text=a_date,
                    font=ctk.CTkFont("Helvetica", 10),
                    text_color=MUTED,
                ).pack(side="left", padx=8)

                ctk.CTkLabel(
                    af, text=a_status.upper(),
                    font=ctk.CTkFont("Helvetica", 9, "bold"),
                    text_color=a_color,
                ).pack(side="right")

        # ── 5. MEMBRESÍA — Cambiar Tier ───────────────
        ctk.CTkLabel(
            self.detail_frame,
            text="🏅  Gestión de Membresía",
            font=ctk.CTkFont("Helvetica", 14, "bold"),
            text_color=GOLD,
        ).pack(anchor="w", padx=10, pady=(14, 6))

        mem_frame = ctk.CTkFrame(self.detail_frame, fg_color="#1a1a1a", corner_radius=8)
        mem_frame.pack(fill="x", padx=10, pady=(0, 16))

        ctk.CTkLabel(
            mem_frame,
            text=f"Tier actual: {tier_label}",
            font=ctk.CTkFont("Helvetica", 12),
            text_color=tier_color,
        ).pack(anchor="w", padx=12, pady=(10, 6))

        btn_row = ctk.CTkFrame(mem_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        for t, label, color in [
            ("none",     "Ninguno", "#555"),
            ("silver",   "Silver",  "#6b7b8d"),
            ("gold",     "Gold",    "#8b6914"),
            ("platinum", "Platinum","#4a5568"),
        ]:
            is_current = (t == tier)
            btn = ctk.CTkButton(
                btn_row,
                text=f"{'● ' if is_current else ''}{label}",
                height=28,
                corner_radius=6,
                fg_color=color if is_current else "#2b2b2b",
                hover_color="#333" if not is_current else color,
                text_color=GOLD if is_current else "#888",
                font=ctk.CTkFont("Helvetica", 10, "bold" if is_current else "normal"),
                command=lambda t=t: self._do_change_membership(t),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)

    def _do_change_membership(self, tier: str) -> None:
        """Llama al callback de cambio de membresía."""
        if self._on_change_membership and self._current_user_id:
            self._on_change_membership(self._current_user_id, tier)

    def _clear_details(self) -> None:
        """Limpia todos los widgets del panel de detalles."""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
