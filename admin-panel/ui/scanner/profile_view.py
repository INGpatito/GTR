"""
Parking GTR — Profile View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Renderizado del perfil VIP completo de un socio,
incluyendo tarjeta, garaje, historial, y botones de check-in/out.
"""

import customtkinter as ctk
from tkinter import messagebox

from config.theme import (
    AMBER, DARK_BG, GOLD, GOLD_SOFT, GREEN, GREEN_HOVER,
    MUTED, PANEL_BG, TIER_EMOJI, VEHICLE_EMOJI,
)


class ProfileView:
    """Renderiza el perfil completo de un socio en el área principal."""

    def __init__(self, main_frame: ctk.CTkFrame):
        self.main = main_frame

    def show_welcome(self) -> None:
        """Muestra la pantalla de bienvenida."""
        self._clear()
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame,
            text="◆",
            font=ctk.CTkFont("Helvetica", 48),
            text_color=GOLD,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text="PARKING GTR",
            font=ctk.CTkFont("Helvetica", 32, "bold"),
            text_color=GOLD,
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Escanea un QR o ingresa el ID del socio\npara ver su perfil completo.",
            font=ctk.CTkFont("Helvetica", 14),
            text_color=MUTED,
            justify="center",
        ).pack(pady=(12, 0))

    def render(self, row, vehicles, activity, card_num, on_checkin=None, on_checkout=None):
        """Renderiza el perfil completo del socio.

        Args:
            row: Tupla (id, full_name, email, phone, service, vehicle,
                        arrival_date, arrival_time, status, created_at).
            vehicles: Lista de vehículos del garaje.
            activity: Historial de actividad reciente.
            card_num: Número de tarjeta formateado.
            on_checkin: Callback(uid, status) para check-in.
            on_checkout: Callback(uid) para check-out.
        """
        (uid, full_name, email, phone, service, vehicle,
         arr_date, arr_time, status, created_at) = row

        self._clear()

        # Contenedor con scroll
        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # ── 1. TARJETA VIP ──
        self._render_vip_card(scroll, uid, full_name, service, card_num, status)

        # ── 2. INFO PERSONAL + CHECK-IN ──
        self._render_info_panel(
            scroll, uid, email, phone, service, status, created_at,
            on_checkin, on_checkout,
        )

        # ── 3. GARAJE ──
        self._render_garage(scroll, vehicles)

        # ── 4. HISTORIAL ──
        self._render_activity(scroll, activity)

    # ──────────────────────────────────────────────────
    #  SECCIONES PRIVADAS
    # ──────────────────────────────────────────────────
    def _render_vip_card(self, parent, uid, name, service, card_num, status):
        card = ctk.CTkFrame(
            parent, fg_color="#111111", corner_radius=16,
            border_width=1, border_color="#3a3010",
        )
        card.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 20), sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        inner.grid_columnconfigure(1, weight=1)

        # Icono
        emoji = TIER_EMOJI.get(service or "", "🔑")
        tier_label = (service or "member").upper()

        ctk.CTkLabel(
            inner, text=emoji, font=ctk.CTkFont("Helvetica", 40),
        ).grid(row=0, column=0, rowspan=3, padx=(0, 20), sticky="n")

        ctk.CTkLabel(
            inner, text=name or "Socio GTR",
            font=ctk.CTkFont("Helvetica", 26, "bold"),
            text_color=GOLD, anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=f"{tier_label} MEMBER  •  GTR-{str(uid).zfill(4)}",
            font=ctk.CTkFont("Helvetica", 11),
            text_color=MUTED, anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=card_num,
            font=ctk.CTkFont("Courier", 18, "bold"),
            text_color="#cacaca", anchor="w",
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        # Badge
        color = {"confirmed": GREEN, "completed": GREEN, "pending": AMBER}.get(
            status or "pending", MUTED
        )
        ctk.CTkLabel(
            inner, text=f"  {(status or 'pending').upper()}  ",
            font=ctk.CTkFont("Helvetica", 10, "bold"),
            text_color="#000", fg_color=color, corner_radius=8,
        ).grid(row=0, column=2, sticky="ne", padx=(8, 0))

    def _render_info_panel(self, parent, uid, email, phone, service, status, created_at, on_checkin, on_checkout):
        frame = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=12)
        frame.grid(row=1, column=0, padx=(0, 10), pady=(0, 16), sticky="nsew")

        ctk.CTkLabel(
            frame, text="👤  Información Personal",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD,
        ).pack(anchor="w", padx=16, pady=(16, 10))

        member_since = created_at.strftime("%d %b %Y") if created_at else "—"
        info_rows = [
            ("Email",         email or "—"),
            ("Teléfono",      phone or "—"),
            ("Miembro desde", member_since),
            ("Servicio",      (service or "—").title()),
        ]
        for label, val in info_rows:
            row_f = ctk.CTkFrame(frame, fg_color="transparent")
            row_f.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                row_f, text=label,
                font=ctk.CTkFont("Helvetica", 11), text_color=MUTED,
                width=100, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row_f, text=val,
                font=ctk.CTkFont("Helvetica", 12), anchor="w",
            ).pack(side="left")

        # Botones
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(16, 16))

        ctk.CTkButton(
            btn_row, text="✅  Check-In",
            height=36, corner_radius=8,
            fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#000",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            command=lambda: on_checkin(uid, status) if on_checkin else None,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="🚪  Check-Out",
            height=36, corner_radius=8,
            fg_color="#333", hover_color="#444",
            font=ctk.CTkFont("Helvetica", 12),
            command=lambda: on_checkout(uid) if on_checkout else None,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _render_garage(self, parent, vehicles):
        frame = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=12)
        frame.grid(row=1, column=1, padx=(10, 0), pady=(0, 16), sticky="nsew")

        ctk.CTkLabel(
            frame, text="🚗  Garaje del Socio",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD,
        ).pack(anchor="w", padx=16, pady=(16, 10))

        if not vehicles:
            ctk.CTkLabel(
                frame, text="Sin vehículos registrados.", text_color=MUTED,
            ).pack(padx=16, pady=20)
            return

        for veh in vehicles:
            (nickname, v_type, brand, model, year, color, plate, is_primary) = veh
            v_emoji = VEHICLE_EMOJI.get(v_type or "", "🚗")
            meta = " · ".join(filter(None, [brand, model, str(year) if year else None]))

            vcard = ctk.CTkFrame(frame, fg_color="#252525", corner_radius=8)
            vcard.pack(fill="x", padx=16, pady=5)

            inner = ctk.CTkFrame(vcard, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            ctk.CTkLabel(
                inner, text=v_emoji, font=ctk.CTkFont("Helvetica", 22),
            ).pack(side="left", padx=(0, 10))

            info_side = ctk.CTkFrame(inner, fg_color="transparent")
            info_side.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                info_side, text=nickname,
                font=ctk.CTkFont("Helvetica", 13, "bold"), anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_side, text=meta or (v_type or "").title(),
                font=ctk.CTkFont("Helvetica", 11), text_color=MUTED, anchor="w",
            ).pack(anchor="w")

            if plate:
                ctk.CTkLabel(
                    info_side, text=f"🪪  {plate}",
                    font=ctk.CTkFont("Helvetica", 11), text_color=GOLD_SOFT, anchor="w",
                ).pack(anchor="w")

            if is_primary:
                ctk.CTkLabel(
                    inner, text="★ Principal",
                    font=ctk.CTkFont("Helvetica", 10), text_color=GOLD,
                ).pack(side="right")

    def _render_activity(self, parent, activity):
        frame = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=12)
        frame.grid(row=2, column=0, columnspan=2, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            frame, text="📋  Historial Reciente",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD,
        ).pack(anchor="w", padx=16, pady=(16, 10))

        if not activity:
            ctk.CTkLabel(
                frame, text="Sin actividad registrada.", text_color=MUTED,
            ).pack(padx=16, pady=(0, 16))
            return

        for act in activity:
            (a_svc, a_status, a_date) = act
            a_color = (
                GREEN if a_status == "completed"
                else AMBER if a_status == "confirmed"
                else MUTED
            )
            a_date_str = a_date.strftime("%d %b %Y") if a_date else ""

            af = ctk.CTkFrame(frame, fg_color="transparent")
            af.pack(fill="x", padx=16, pady=3)

            ctk.CTkLabel(
                af, text="◆",
                font=ctk.CTkFont("Helvetica", 8), text_color=a_color,
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                af, text=(a_svc or "reservación").title(),
                font=ctk.CTkFont("Helvetica", 12), anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                af, text=a_date_str,
                font=ctk.CTkFont("Helvetica", 11), text_color=MUTED,
            ).pack(side="left", padx=12)

            ctk.CTkLabel(
                af, text=(a_status or "—").upper(),
                font=ctk.CTkFont("Helvetica", 10, "bold"), text_color=a_color,
            ).pack(side="right")

        ctk.CTkFrame(frame, fg_color="transparent", height=12).pack()

    def _clear(self) -> None:
        for w in self.main.winfo_children():
            w.destroy()
