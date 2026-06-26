"""
Parking GTR — Profile View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Renderizado del perfil VIP completo de un socio,
incluyendo tarjeta, garaje, historial, botones de parking,
y selector visual de 24 espacios en 3 pisos.
"""

import customtkinter as ctk
from tkinter import messagebox

from config.theme import (
    AMBER, DARK_BG, GOLD, GOLD_SOFT, GREEN, GREEN_HOVER,
    MUTED, PANEL_BG, TIER_EMOJI, VEHICLE_EMOJI, RED, RED_HOVER,
)


class ProfileView:
    """Renderiza el perfil completo de un socio en el área principal."""

    def __init__(self, main_frame: ctk.CTkFrame):
        self.main = main_frame
        self._pending_requests_widgets = []

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

    def render(self, row, vehicles, activity, card_num,
               on_checkin=None, on_checkout=None, on_close=None, on_force_close_tablet=None,
               on_show_spots=None, parking_spots=None,
               pending_requests=None, on_approve_request=None,
               on_reject_request=None, on_free_spot=None):
        """Renderiza el perfil completo del socio.

        Args:
            row: Tupla (id, full_name, email, phone, service, vehicle,
                        arrival_date, arrival_time, status, created_at).
            vehicles: Lista de vehículos del garaje.
            activity: Historial de actividad reciente.
            card_num: Número de tarjeta formateado.
            on_checkin: Callback(uid, status) para Skip.
            on_checkout: Callback(uid) para check-out.
            on_close: Callback() para cerrar y volver a bienvenida.
            on_show_spots: Callback(uid, vehicle_id) para mostrar selector de spots.
            parking_spots: Lista de spots para el selector visual.
            pending_requests: Lista de solicitudes pendientes del Android.
            on_approve_request: Callback(request_id, spot_id) para aprobar.
            on_reject_request: Callback(request_id) para rechazar.
            on_free_spot: Callback(spot_id) para liberar un spot manualmente.
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

        # ── 2. INFO PERSONAL + BOTONES ──
        self._render_info_panel(
            scroll, uid, email, phone, service, status, created_at,
            on_checkin, on_checkout, on_close, on_force_close_tablet
        )

        # ── 3. GARAJE ──
        self._render_garage(scroll, vehicles)

        # ── 4. SOLICITUDES PENDIENTES ──
        if pending_requests:
            self._render_pending_requests(
                scroll, pending_requests, on_approve_request, on_reject_request
            )

        # ── 5. SELECTOR DE SPOTS (si se pidió) ──
        if parking_spots is not None:
            self._render_spots_selector(
                scroll, parking_spots, on_approve_request, pending_requests, uid, on_free_spot
            )

        # ── 6. HISTORIAL ──
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

    def _render_info_panel(self, parent, uid, email, phone, service, status,
                           created_at, on_checkin, on_checkout, on_close, on_force_close_tablet=None):
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

        # Botones — Skip + Check-Out + Cerrar + Cerrar Tablet
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(16, 16))

        # First row of buttons
        btn_row1 = ctk.CTkFrame(btn_row, fg_color="transparent")
        btn_row1.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            btn_row1, text="⏭  Skip",
            height=36, corner_radius=8,
            fg_color="#333", hover_color="#444",
            font=ctk.CTkFont("Helvetica", 12),
            command=lambda: on_checkin(uid, status) if on_checkin else None,
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        ctk.CTkButton(
            btn_row1, text="🚪  Check-Out",
            height=36, corner_radius=8,
            fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#000",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            command=lambda: on_checkout(uid) if on_checkout else None,
        ).pack(side="left", expand=True, fill="x", padx=(2, 0))

        # Second row of buttons
        btn_row2 = ctk.CTkFrame(btn_row, fg_color="transparent")
        btn_row2.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_row2, text="✕  Cerrar Perfil",
            height=36, corner_radius=8,
            fg_color=RED, hover_color=RED_HOVER, text_color="#fff",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            command=lambda: on_close() if on_close else None,
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        if on_force_close_tablet:
            ctk.CTkButton(
                btn_row2, text="📱 Cerrar Tablet",
                height=36, corner_radius=8,
                fg_color="#8F7322", hover_color="#6F581A", text_color="#fff",
                font=ctk.CTkFont("Helvetica", 12, "bold"),
                command=on_force_close_tablet,
            ).pack(side="left", expand=True, fill="x", padx=(2, 0))

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

    def _render_pending_requests(self, parent, pending_requests, on_approve, on_reject):
        """Renderiza solicitudes pendientes del Android."""
        frame = ctk.CTkFrame(parent, fg_color="#1a0f0f", corner_radius=12,
                             border_width=2, border_color=AMBER)
        frame.grid(row=2, column=0, columnspan=2, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            frame, text="🔔  Solicitudes Pendientes del Android",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=AMBER,
        ).pack(anchor="w", padx=16, pady=(16, 10))

        for req in pending_requests:
            # req: (id, user_id, vehicle_id, request_type, status, created_at,
            #        full_name, email, vehicle_nickname, brand, model, plate, vehicle_type)
            req_id = req[0]
            req_type = req[3]
            full_name = req[6]
            veh_nick = req[8] or "—"
            veh_brand = req[9] or ""
            veh_model = req[10] or ""
            veh_plate = req[11] or "—"

            if req_type == "check_in":
                type_label = "🅿️ INGRESAR"
                type_color = GREEN
            elif req_type == "check_out":
                type_label = "🚪 RETIRAR"
                type_color = AMBER
            elif req_type == "heliport":
                type_label = "🚁 HELIPUERTO"
                type_color = "#3498db"
            else:
                type_label = req_type.upper()
                type_color = MUTED

            req_frame = ctk.CTkFrame(frame, fg_color="#252525", corner_radius=8)
            req_frame.pack(fill="x", padx=16, pady=5)

            req_inner = ctk.CTkFrame(req_frame, fg_color="transparent")
            req_inner.pack(fill="x", padx=12, pady=10)

            # Info
            info_col = ctk.CTkFrame(req_inner, fg_color="transparent")
            info_col.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                info_col, text=f"{full_name}  —  {type_label}",
                font=ctk.CTkFont("Helvetica", 13, "bold"),
                text_color=type_color, anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_col,
                text=f"Vehículo: {veh_nick} ({veh_brand} {veh_model})  •  Placa: {veh_plate}",
                font=ctk.CTkFont("Helvetica", 11),
                text_color=MUTED, anchor="w",
            ).pack(anchor="w")

            # Buttons
            btn_col = ctk.CTkFrame(req_inner, fg_color="transparent")
            btn_col.pack(side="right")

            ctk.CTkButton(
                btn_col, text="✅ Aceptar",
                height=30, corner_radius=6,
                fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#000",
                font=ctk.CTkFont("Helvetica", 11, "bold"),
                command=lambda rid=req_id, rtype=req_type: on_approve(rid, rtype, None) if on_approve else None,
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                btn_col, text="❌ Rechazar",
                height=30, corner_radius=6,
                fg_color=RED, hover_color=RED_HOVER, text_color="#fff",
                font=ctk.CTkFont("Helvetica", 11),
                command=lambda rid=req_id: on_reject(rid) if on_reject else None,
            ).pack(side="left")

        ctk.CTkFrame(frame, fg_color="transparent", height=8).pack()

    def _render_spots_selector(self, parent, spots, on_select_spot, pending_requests, current_uid, on_free_spot):
        """Renderiza el selector visual de 24 spots en 3 pisos."""
        frame = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=12)
        frame.grid(row=3, column=0, columnspan=2, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            frame, text="🅿️  Mapa de Estacionamiento  —  24 Espacios",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            frame,
            text="🟢 Disponible    🔴 Ocupado    ⚙️ Mantenimiento",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Get the first pending check_in request ID for the approve callback
        pending_checkin_id = None
        if pending_requests:
            for req in pending_requests:
                if req[3] == "check_in":
                    pending_checkin_id = req[0]
                    break

        # Organize spots by floor
        floors = {1: [], 2: [], 3: []}
        for spot in spots:
            # spot: (id, spot_number, floor, spot_label, status, ...)
            spot_floor = spot[2]
            if spot_floor in floors:
                floors[spot_floor].append(spot)

        for floor_num in [1, 2, 3]:
            floor_frame = ctk.CTkFrame(frame, fg_color="#1a1a1a", corner_radius=8)
            floor_frame.pack(fill="x", padx=16, pady=5)

            ctk.CTkLabel(
                floor_frame,
                text=f"PISO {floor_num}",
                font=ctk.CTkFont("Helvetica", 11, "bold"),
                text_color=GOLD,
            ).pack(anchor="w", padx=12, pady=(8, 4))

            spots_row = ctk.CTkFrame(floor_frame, fg_color="transparent")
            spots_row.pack(fill="x", padx=12, pady=(0, 8))

            for spot in floors.get(floor_num, []):
                spot_id = spot[0]
                spot_label = spot[3]
                spot_status = spot[4]
                user_name = spot[8] if len(spot) > 8 else None
                vehicle_nick = spot[9] if len(spot) > 9 else None

                if spot_status == "available":
                    bg_color = GREEN
                    hover_color = GREEN_HOVER
                    text_col = "#000"
                    label_text = f"🚗\n{spot_label}"
                    clickable = True
                    btn_cmd = (lambda sid=spot_id, pcid=pending_checkin_id:
                               on_select_spot(pcid, "check_in", sid) if on_select_spot and pcid else None)
                elif spot_status == "occupied":
                    bg_color = RED
                    hover_color = RED_HOVER
                    text_col = "#fff"
                    occ_name = (user_name or "")[:8]
                    label_text = f"🔒\n{spot_label}\n{occ_name}"
                    
                    occupied_by_uid = spot[5]
                    if occupied_by_uid == current_uid and on_free_spot:
                        clickable = True
                        btn_cmd = (lambda sid=spot_id: on_free_spot(sid))
                    else:
                        clickable = False
                        btn_cmd = lambda: None
                else:
                    bg_color = "#555"
                    hover_color = "#666"
                    text_col = "#ccc"
                    label_text = f"⚙️\n{spot_label}"
                    clickable = False
                    btn_cmd = lambda: None

                btn = ctk.CTkButton(
                    spots_row,
                    text=label_text,
                    width=90, height=70,
                    corner_radius=8,
                    fg_color=bg_color,
                    hover_color=hover_color if clickable else bg_color,
                    text_color=text_col,
                    font=ctk.CTkFont("Helvetica", 10, "bold"),
                    command=btn_cmd if clickable else lambda: None,
                    state="normal" if clickable else "disabled",
                )
                btn.pack(side="left", padx=3, pady=2)

        ctk.CTkFrame(frame, fg_color="transparent", height=8).pack()

    def _render_activity(self, parent, activity):
        frame = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=12)
        frame.grid(row=4, column=0, columnspan=2, pady=(0, 16), sticky="ew")

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
