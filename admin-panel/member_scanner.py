"""
╔══════════════════════════════════════════════════════╗
║          PARKING GTR — MEMBER SCANNER v1.0           ║
║   Busca socios por ID o código QR · Direct DB        ║
╚══════════════════════════════════════════════════════╝

Uso:
  python member_scanner.py

Próximamente:
  - Cámara web para leer QR físicamente (OpenCV)
  - Sensor RFID / ultrasónico (GPIO)

Requisitos:
  pip install customtkinter psycopg2-binary python-dotenv bcrypt winsound
"""

import customtkinter as ctk
import psycopg2
from psycopg2 import Error as PGError
from tkinter import messagebox
import threading
import datetime
import hmac
import hashlib
import os
import sys

# ---------- Intentar sonido (Windows) ----------
try:
    import winsound
    SOUND_OK = True
except ImportError:
    SOUND_OK = False

# ---------- Env ----------
from dotenv import load_dotenv
_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_dir, ".env"))

JWT_SECRET = os.getenv("JWT_SECRET", "fallback_dev_secret_change_me")

# ═══════════════════════════════════════════════════════
#  HMAC — Replica la misma lógica que backend/server.js
# ═══════════════════════════════════════════════════════
def generate_card_number(member_id: int) -> str:
    """Genera el número cifrado de 16 dígitos idéntico al backend Node.js."""
    msg = f"GTR-CARD-{member_id}".encode()
    key = JWT_SECRET.encode()
    hex_digest = hmac.new(key, msg, hashlib.sha256).hexdigest()  # 64 hex chars
    digits = ""
    i = 0
    while len(digits) < 16 and i < 48:
        num = int(hex_digest[i:i+3], 16) % 10
        digits += str(num)
        i += 3
    while len(digits) < 16:
        digits += "0"
    return f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"


# ═══════════════════════════════════════════════════════
#  COLORES & TEMA
# ═══════════════════════════════════════════════════════
GOLD       = "#d4af37"
GOLD_SOFT  = "#c8bc98"
DARK_BG    = "#0d0d0d"
CARD_BG    = "#161616"
PANEL_BG   = "#1e1e1e"
MUTED      = "#666666"
GREEN      = "#2ecc71"
RED        = "#e74c3c"
AMBER      = "#f39c12"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ═══════════════════════════════════════════════════════
#  DB HELPER
# ═══════════════════════════════════════════════════════
DB_PARAMS = {
    "host":     os.getenv("DB_HOST",     "192.168.100.61"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME",     "parking_gtr"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_conn():
    return psycopg2.connect(**DB_PARAMS)


# ═══════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════
class MemberScanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Parking GTR — Member Scanner")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        # Estado actual
        self.current_member_id: int | None = None

        # ── Layout principal: sidebar | contenido
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    # ─────────────────────────────────────────────────
    #  SIDEBAR
    # ─────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=260, fg_color=CARD_BG, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(99, weight=1)

        # Logo
        ctk.CTkLabel(
            sb, text="▲ GTR",
            font=ctk.CTkFont("Helvetica", 28, "bold"),
            text_color=GOLD
        ).grid(row=0, column=0, padx=24, pady=(28, 4), sticky="w")

        ctk.CTkLabel(
            sb, text="MEMBER SCANNER",
            font=ctk.CTkFont("Helvetica", 10), text_color=MUTED
        ).grid(row=1, column=0, padx=26, pady=(0, 24), sticky="w")

        # ── Sección: Ingresar ID del Socio
        self._sidebar_section(sb, row=2, text="BÚSQUEDA MANUAL")

        self.id_entry = ctk.CTkEntry(
            sb,
            placeholder_text="Num. de Socio  (ej: 23)",
            font=ctk.CTkFont("Helvetica", 13),
            height=40, corner_radius=8,
            border_color=GOLD, border_width=1,
        )
        self.id_entry.grid(row=3, column=0, padx=16, pady=(4, 8), sticky="ew")
        self.id_entry.bind("<Return>", lambda e: self._search_by_id())

        ctk.CTkButton(
            sb, text="🔍  Buscar por ID",
            height=38, corner_radius=8,
            fg_color=GOLD, text_color="#000",
            hover_color="#b5952f",
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._search_by_id
        ).grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")

        # ── Sección: Ingresar número de tarjeta QR
        self._sidebar_section(sb, row=5, text="CÓDIGO QR (TEXTO)")

        self.qr_entry = ctk.CTkEntry(
            sb,
            placeholder_text="Pega el número de tarjeta",
            font=ctk.CTkFont("Helvetica", 13),
            height=40, corner_radius=8,
            border_color="#4a4a4a", border_width=1,
        )
        self.qr_entry.grid(row=6, column=0, padx=16, pady=(4, 8), sticky="ew")
        self.qr_entry.bind("<Return>", lambda e: self._search_by_qr())

        ctk.CTkButton(
            sb, text="📇  Verificar QR",
            height=38, corner_radius=8,
            fg_color="#2b2b2b", text_color=GOLD_SOFT,
            hover_color="#3a3a3a",
            border_color="#444", border_width=1,
            font=ctk.CTkFont("Helvetica", 13),
            command=self._search_by_qr
        ).grid(row=7, column=0, padx=16, pady=(0, 24), sticky="ew")

        # ── Sección Sensor (stub)
        self._sidebar_section(sb, row=8, text="SENSORES (PRÓXIMAMENTE)")

        sensor_frame = ctk.CTkFrame(sb, fg_color="#1a1a1a", corner_radius=8)
        sensor_frame.grid(row=9, column=0, padx=16, pady=(4, 24), sticky="ew")

        ctk.CTkLabel(
            sensor_frame,
            text="🔌  Sin sensor conectado",
            font=ctk.CTkFont("Helvetica", 11),
            text_color=MUTED
        ).pack(padx=12, pady=10)

        # Simular lectura de sensor (para pruebas)
        ctk.CTkButton(
            sensor_frame,
            text="▶ Simular Lectura",
            height=30, corner_radius=6,
            fg_color="#2b2b2b", text_color="#888",
            hover_color="#333",
            font=ctk.CTkFont("Helvetica", 11),
            command=self._simulate_sensor
        ).pack(padx=12, pady=(0, 10), fill="x")

        # ── Estado DB al fondo
        self.db_status = ctk.CTkLabel(
            sb, text="● Sin conexión",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=MUTED
        )
        self.db_status.grid(row=99, column=0, padx=16, pady=16, sticky="sw")

    def _sidebar_section(self, parent, row: int, text: str):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont("Helvetica", 9, "bold"),
            text_color=GOLD
        ).grid(row=row, column=0, padx=20, pady=(8, 0), sticky="w")

    # ─────────────────────────────────────────────────
    #  ÁREA PRINCIPAL
    # ─────────────────────────────────────────────────
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=DARK_BG)
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)
        self._show_welcome()

    def _clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ─────────────────────────────────────────────────
    #  PANTALLA BIENVENIDA
    # ─────────────────────────────────────────────────
    def _show_welcome(self):
        self._clear_main()
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text="◆",
            font=ctk.CTkFont("Helvetica", 48),
            text_color=GOLD
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            frame, text="PARKING GTR",
            font=ctk.CTkFont("Helvetica", 32, "bold"),
            text_color=GOLD
        ).pack()

        ctk.CTkLabel(
            frame, text="Escanea un QR o ingresa el ID del socio\npara ver su perfil completo.",
            font=ctk.CTkFont("Helvetica", 14),
            text_color=MUTED, justify="center"
        ).pack(pady=(12, 0))

    # ─────────────────────────────────────────────────
    #  BÚSQUEDA POR ID NUMÉRICO
    # ─────────────────────────────────────────────────
    def _search_by_id(self):
        raw = self.id_entry.get().strip().replace("GTR-", "").replace("gtr-", "")
        if not raw.isdigit():
            messagebox.showwarning("Entrada inválida", "Ingresa solo el número de socio (ej: 23).")
            return
        self._fetch_and_show(int(raw))

    # ─────────────────────────────────────────────────
    #  BÚSQUEDA POR NÚMERO DE TARJETA QR (ENCRIPTADO)
    # ─────────────────────────────────────────────────
    def _search_by_qr(self):
        raw = self.qr_entry.get().strip().replace(" ", "")
        if not raw:
            messagebox.showwarning("Campo vacío", "Pega el número de tarjeta del QR.")
            return

        # Buscar qué ID de socio genera ese número HMAC
        self.db_status.configure(text="● Verificando tarjeta...", text_color=AMBER)
        self.update()

        def _verify():
            conn = None
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT id FROM reservations WHERE password_hash IS NOT NULL ORDER BY id")
                ids = [r[0] for r in cur.fetchall()]

                matched_id = None
                for mid in ids:
                    if generate_card_number(mid).replace(" ", "") == raw:
                        matched_id = mid
                        break

                if matched_id:
                    self.after(0, lambda: self._fetch_and_show(matched_id))
                else:
                    self.after(0, lambda: [
                        self.db_status.configure(text="● QR inválido", text_color=RED),
                        messagebox.showerror("QR Inválido", "No se encontró ningún socio con esa tarjeta.\n\nVerifica que el número sea correcto.")
                    ])
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error DB", str(e)))
            finally:
                if conn:
                    conn.close()

        threading.Thread(target=_verify, daemon=True).start()

    # ─────────────────────────────────────────────────
    #  SIMULADOR DE SENSOR
    # ─────────────────────────────────────────────────
    def _simulate_sensor(self):
        """
        Stub para integración futura de sensores físicos.
        En el futuro, este método será llamado por un thread
        que escucha datos de GPIO/RFID en lugar del botón.
        """
        dialog = ctk.CTkInputDialog(
            text="[MODO SIMULACIÓN]\nIntroduce el ID del socio como si lo hubiera leído el sensor:",
            title="Simular Sensor"
        )
        val = dialog.get_input()
        if val and val.strip().isdigit():
            self._fetch_and_show(int(val.strip()))

    # ─────────────────────────────────────────────────
    #  CARGA DE DATOS DESDE DB
    # ─────────────────────────────────────────────────
    def _fetch_and_show(self, member_id: int):
        self.db_status.configure(text="● Conectando...", text_color=AMBER)
        self.update()

        def _load():
            conn = None
            try:
                conn = get_conn()
                cur = conn.cursor()

                # ── Datos principales
                cur.execute("""
                    SELECT id, full_name, email, phone, service, vehicle,
                           arrival_date, arrival_time, status, created_at
                    FROM reservations
                    WHERE id = %s
                """, (member_id,))
                row = cur.fetchone()

                if not row:
                    self.after(0, lambda: [
                        self.db_status.configure(text="● No encontrado", text_color=RED),
                        messagebox.showwarning("Socio no encontrado", f"No existe ningún socio con ID {member_id}.")
                    ])
                    return

                # ── Vehículos registrados
                cur.execute("""
                    SELECT nickname, vehicle, brand, model, year, color, plate, is_primary
                    FROM user_vehicles
                    WHERE user_id = %s
                    ORDER BY is_primary DESC, created_at ASC
                """, (member_id,))
                vehicles = cur.fetchall()

                # ── Historial de actividad
                cur.execute("""
                    SELECT service, status, created_at
                    FROM reservations
                    WHERE id != %s AND email = (SELECT email FROM reservations WHERE id = %s)
                    ORDER BY created_at DESC LIMIT 10
                """, (member_id, member_id))
                activity = cur.fetchall()

                card_num = generate_card_number(member_id)
                self.after(0, lambda: self._render_profile(row, vehicles, activity, card_num))

            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: [
                    self.db_status.configure(text="● Error DB", text_color=RED),
                    messagebox.showerror("Error de base de datos", err_msg)
                ])
            finally:
                if conn:
                    conn.close()

        threading.Thread(target=_load, daemon=True).start()

    # ─────────────────────────────────────────────────
    #  RENDERIZAR PERFIL
    # ─────────────────────────────────────────────────
    def _render_profile(self, row, vehicles, activity, card_num):
        (uid, full_name, email, phone, service, vehicle,
         arr_date, arr_time, status, created_at) = row

        self.current_member_id = uid
        self._clear_main()

        # Sonido de bienvenida
        self._chime()

        self.db_status.configure(
            text=f"● GTR-{str(uid).zfill(4)} cargado",
            text_color=GREEN
        )

        # Contenedor con scroll
        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # ── 1. TARJETA VIP ────────────────────────────
        card_frame = ctk.CTkFrame(
            scroll, fg_color="#111111", corner_radius=16,
            border_width=1, border_color="#3a3010"
        )
        card_frame.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 20), sticky="ew")

        cf_inner = ctk.CTkFrame(card_frame, fg_color="transparent")
        cf_inner.pack(fill="x", padx=24, pady=20)
        cf_inner.grid_columnconfigure(1, weight=1)

        # Icono de tier
        tier_emoji = {"valet": "🤵", "monthly": "📅", "concierge": "⭐", "fleet": "🏢", "event": "🎭"}.get(service or "", "🔑")
        tier_label = (service or "member").upper()

        ctk.CTkLabel(
            cf_inner, text=tier_emoji,
            font=ctk.CTkFont("Helvetica", 40)
        ).grid(row=0, column=0, rowspan=3, padx=(0, 20), sticky="n")

        ctk.CTkLabel(
            cf_inner, text=full_name or "Socio GTR",
            font=ctk.CTkFont("Helvetica", 26, "bold"),
            text_color=GOLD, anchor="w"
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            cf_inner, text=f"{tier_label} MEMBER  •  GTR-{str(uid).zfill(4)}",
            font=ctk.CTkFont("Helvetica", 11),
            text_color=MUTED, anchor="w"
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            cf_inner, text=card_num,
            font=ctk.CTkFont("Courier", 18, "bold"),
            text_color="#cacaca", anchor="w"
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        # Badge de estado
        status_color = {"confirmed": GREEN, "completed": GREEN, "pending": AMBER}.get(status or "pending", MUTED)
        ctk.CTkLabel(
            cf_inner, text=f"  {(status or 'pending').upper()}  ",
            font=ctk.CTkFont("Helvetica", 10, "bold"),
            text_color="#000", fg_color=status_color, corner_radius=8
        ).grid(row=0, column=2, sticky="ne", padx=(8, 0))

        # ── 2. INFO PERSONAL + CHECK-IN ───────────────
        info_frame = ctk.CTkFrame(scroll, fg_color=PANEL_BG, corner_radius=12)
        info_frame.grid(row=1, column=0, padx=(0, 10), pady=(0, 16), sticky="nsew")

        ctk.CTkLabel(
            info_frame, text="👤  Información Personal",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD
        ).pack(anchor="w", padx=16, pady=(16, 10))

        member_since = created_at.strftime("%d %b %Y") if created_at else "—"
        info_rows = [
            ("Email",        email  or "—"),
            ("Teléfono",     phone  or "—"),
            ("Miembro desde", member_since),
            ("Servicio",     (service or "—").title()),
        ]
        for label, val in info_rows:
            row_f = ctk.CTkFrame(info_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row_f, text=label, font=ctk.CTkFont("Helvetica", 11), text_color=MUTED, width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row_f, text=val,   font=ctk.CTkFont("Helvetica", 12), anchor="w").pack(side="left")

        # ── Botones de acción
        btn_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(16, 16))

        ctk.CTkButton(
            btn_row, text="✅  Check-In",
            height=36, corner_radius=8,
            fg_color=GREEN, hover_color="#27ae60", text_color="#000",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            command=lambda: self._checkin(uid, status)
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="🚪  Check-Out",
            height=36, corner_radius=8,
            fg_color="#333", hover_color="#444",
            font=ctk.CTkFont("Helvetica", 12),
            command=lambda: self._checkout(uid)
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        # ── 3. GARAJE ─────────────────────────────────
        garage_frame = ctk.CTkFrame(scroll, fg_color=PANEL_BG, corner_radius=12)
        garage_frame.grid(row=1, column=1, padx=(10, 0), pady=(0, 16), sticky="nsew")

        ctk.CTkLabel(
            garage_frame, text="🚗  Garaje del Socio",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD
        ).pack(anchor="w", padx=16, pady=(16, 10))

        if not vehicles:
            ctk.CTkLabel(
                garage_frame, text="Sin vehículos registrados.",
                text_color=MUTED
            ).pack(padx=16, pady=20)
        else:
            for veh in vehicles:
                (nickname, v_type, brand, model, year, color, plate, is_primary) = veh
                v_emoji = {"sports": "🏎", "suv": "🚙", "sedan": "🚗", "convertible": "🚘", "exotic": "🏆"}.get(v_type or "", "🚗")
                meta = " · ".join(filter(None, [brand, model, str(year) if year else None]))

                vcard = ctk.CTkFrame(garage_frame, fg_color="#252525", corner_radius=8)
                vcard.pack(fill="x", padx=16, pady=5)

                vcard_inner = ctk.CTkFrame(vcard, fg_color="transparent")
                vcard_inner.pack(fill="x", padx=12, pady=10)

                ctk.CTkLabel(vcard_inner, text=v_emoji, font=ctk.CTkFont("Helvetica", 22)).pack(side="left", padx=(0, 10))

                info_side = ctk.CTkFrame(vcard_inner, fg_color="transparent")
                info_side.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(info_side, text=nickname,  font=ctk.CTkFont("Helvetica", 13, "bold"), anchor="w").pack(anchor="w")
                ctk.CTkLabel(info_side, text=meta or (v_type or "").title(), font=ctk.CTkFont("Helvetica", 11), text_color=MUTED, anchor="w").pack(anchor="w")
                if plate:
                    ctk.CTkLabel(info_side, text=f"🪪  {plate}", font=ctk.CTkFont("Helvetica", 11), text_color=GOLD_SOFT, anchor="w").pack(anchor="w")

                if is_primary:
                    ctk.CTkLabel(vcard_inner, text="★ Principal", font=ctk.CTkFont("Helvetica", 10), text_color=GOLD).pack(side="right")

        # ── 4. HISTORIAL DE ACTIVIDAD ─────────────────
        act_frame = ctk.CTkFrame(scroll, fg_color=PANEL_BG, corner_radius=12)
        act_frame.grid(row=2, column=0, columnspan=2, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(
            act_frame, text="📋  Historial Reciente",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=GOLD
        ).pack(anchor="w", padx=16, pady=(16, 10))

        if not activity:
            ctk.CTkLabel(act_frame, text="Sin actividad registrada.", text_color=MUTED).pack(padx=16, pady=(0, 16))
        else:
            for act in activity:
                (a_svc, a_status, a_date) = act
                a_color = GREEN if a_status == "completed" else AMBER if a_status == "confirmed" else MUTED
                a_date_str = a_date.strftime("%d %b %Y") if a_date else ""

                af = ctk.CTkFrame(act_frame, fg_color="transparent")
                af.pack(fill="x", padx=16, pady=3)

                ctk.CTkLabel(af, text="◆", font=ctk.CTkFont("Helvetica", 8), text_color=a_color).pack(side="left", padx=(0, 8))
                ctk.CTkLabel(af, text=(a_svc or "reservación").title(), font=ctk.CTkFont("Helvetica", 12), anchor="w").pack(side="left")
                ctk.CTkLabel(af, text=a_date_str, font=ctk.CTkFont("Helvetica", 11), text_color=MUTED).pack(side="left", padx=12)
                ctk.CTkLabel(af, text=(a_status or "—").upper(), font=ctk.CTkFont("Helvetica", 10, "bold"), text_color=a_color).pack(side="right")

            ctk.CTkFrame(act_frame, fg_color="transparent", height=12).pack()

    # ─────────────────────────────────────────────────
    #  CHECK-IN / CHECK-OUT
    # ─────────────────────────────────────────────────
    def _checkin(self, uid: int, current_status: str):
        if current_status == "confirmed":
            messagebox.showinfo("Ya en Vault", "Este socio ya tiene un check-in activo.")
            return
        self._update_status(uid, "confirmed", f"✅ Check-In registrado para GTR-{str(uid).zfill(4)}.")

    def _checkout(self, uid: int):
        self._update_status(uid, "completed", f"🚪 Check-Out registrado para GTR-{str(uid).zfill(4)}.")

    def _update_status(self, uid: int, new_status: str, msg: str):
        def _do():
            conn = None
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("UPDATE reservations SET status = %s WHERE id = %s", (new_status, uid))
                conn.commit()
                self.after(0, lambda: [
                    messagebox.showinfo("Actualizado", msg),
                    self._fetch_and_show(uid)
                ])
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error DB", str(e)))
            finally:
                if conn:
                    conn.close()
        threading.Thread(target=_do, daemon=True).start()

    # ─────────────────────────────────────────────────
    #  CHIME DE BIENVENIDA
    # ─────────────────────────────────────────────────
    def _chime(self):
        """Toca un chime de bienvenida de lujo en Windows."""
        if not SOUND_OK:
            return
        def _play():
            try:
                winsound.Beep(880, 120)
                winsound.Beep(1109, 120)
                winsound.Beep(1318, 200)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()


# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MemberScanner()
    app.mainloop()
