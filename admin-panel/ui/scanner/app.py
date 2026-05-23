"""
Parking GTR — Member Scanner Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana principal del scanner de socios.
Busca miembros por número de tarjeta, ID, o sensor.
"""

import threading

import customtkinter as ctk
from tkinter import messagebox

from config.settings import print_startup_banner
from config.theme import AMBER, DARK_BG, GREEN, RED, setup_ctk_theme
from core.crypto import generate_card_number
from services import reservation_service, member_service, vehicle_service
from ui.scanner.sidebar import ScannerSidebar
from ui.scanner.profile_view import ProfileView
from utils.sound import play_chime

# Configurar tema global
setup_ctk_theme()


class MemberScanner(ctk.CTk):
    """Ventana principal del scanner de socios de Parking GTR."""

    def __init__(self):
        super().__init__()
        print_startup_banner("Member Scanner")

        self.title("Parking GTR — Member Scanner")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        self.current_member_id: int | None = None

        # ── Layout ──
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = ScannerSidebar(
            self,
            callbacks={
                "search_card": self._search_by_card,
                "search_id":   self._search_by_id,
                "simulate":    self._simulate_sensor,
            },
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main Area ──
        main_frame = ctk.CTkFrame(self, fg_color=DARK_BG)
        main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.profile_view = ProfileView(main_frame)
        self.profile_view.show_welcome()

    # ══════════════════════════════════════════════════
    #  BÚSQUEDA POR TARJETA
    # ══════════════════════════════════════════════════
    def _search_by_card(self, raw_input: str) -> None:
        """Busca un socio por número de tarjeta de 16 dígitos."""
        raw = raw_input.replace(" ", "").replace("-", "")
        if not raw:
            messagebox.showwarning("Campo vacío", "Ingresa el número de tu tarjeta GTR.")
            return
        if not raw.isdigit() or len(raw) != 16:
            messagebox.showwarning(
                "Formato incorrecto",
                "El número de tarjeta debe tener 16 dígitos.\n"
                "Ejemplo: 1234 5678 9012 3456",
            )
            return
        self._verify_card_number(raw)

    def _verify_card_number(self, digits_clean: str) -> None:
        """Verifica el número HMAC contra todos los socios en DB."""
        self.sidebar.db_status.set_status("● Verificando...", AMBER)
        self.update()

        def _verify():
            try:
                ids = member_service.get_all_member_ids()
                print(f"[DEBUG] Buscando tarjeta: {digits_clean}")
                print(f"[DEBUG] Total IDs en DB: {len(ids)}")

                matched_id = None
                for mid in ids:
                    generated = generate_card_number(mid).replace(" ", "")
                    if generated == digits_clean:
                        matched_id = mid
                        print(f"[DEBUG] ¡Match! ID={mid} → {generated}")
                        break

                if not matched_id:
                    sample = [(mid, generate_card_number(mid)) for mid in ids[:3]]
                    print("[DEBUG] No hubo match. Primeros 3 números generados:")
                    for mid, cn in sample:
                        print(f"  ID {mid} → {cn}")

                if matched_id:
                    self.after(0, lambda: self._fetch_and_show(matched_id))
                else:
                    self.after(0, lambda: [
                        self.sidebar.db_status.set_status("● Tarjeta no válida", RED),
                        messagebox.showerror(
                            "Tarjeta No Reconocida",
                            "Ese número de tarjeta no pertenece a ningún socio GTR.\n\n"
                            "Verifica que hayas escrito los 16 dígitos correctamente.",
                        ),
                    ])
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        threading.Thread(target=_verify, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  BÚSQUEDA POR ID
    # ══════════════════════════════════════════════════
    def _search_by_id(self, raw_input: str) -> None:
        """Busca un socio por ID numérico."""
        cleaned = raw_input.replace("GTR-", "").replace("gtr-", "")
        if not cleaned.isdigit():
            messagebox.showwarning(
                "Entrada inválida",
                "Ingresa solo el número interno de socio (ej: 23).",
            )
            return
        self._fetch_and_show(int(cleaned))

    # ══════════════════════════════════════════════════
    #  SIMULADOR DE SENSOR
    # ══════════════════════════════════════════════════
    def _simulate_sensor(self) -> None:
        """Simula la lectura de un sensor con input manual."""
        dialog = ctk.CTkInputDialog(
            text="[MODO SIMULACIÓN]\nIntroduce el ID del socio como si lo hubiera leído el sensor:",
            title="Simular Sensor",
        )
        val = dialog.get_input()
        if val and val.strip().isdigit():
            self._fetch_and_show(int(val.strip()))

    # ══════════════════════════════════════════════════
    #  FETCH & RENDER
    # ══════════════════════════════════════════════════
    def _fetch_and_show(self, member_id: int) -> None:
        """Carga datos del socio y renderiza su perfil."""
        self.sidebar.db_status.set_status("● Conectando...", AMBER)
        self.update()

        def _load():
            try:
                row = reservation_service.get_reservation_by_id(member_id)
                if not row:
                    self.after(0, lambda: [
                        self.sidebar.db_status.set_status("● No encontrado", RED),
                        messagebox.showwarning(
                            "Socio no encontrado",
                            f"No existe ningún socio con ID {member_id}.",
                        ),
                    ])
                    return

                vehicles = vehicle_service.get_user_vehicles(member_id)
                activity = vehicle_service.get_activity_history(member_id)
                card_num = generate_card_number(member_id)

                self.after(0, lambda: self._render_profile(row, vehicles, activity, card_num))

            except Exception as exc:
                err_msg = str(exc)
                self.after(0, lambda: [
                    self.sidebar.db_status.set_status("● Error DB", RED),
                    messagebox.showerror("Error de base de datos", err_msg),
                ])

        threading.Thread(target=_load, daemon=True).start()

    def _render_profile(self, row, vehicles, activity, card_num) -> None:
        """Renderiza el perfil y actualiza estado."""
        uid = row[0]
        self.current_member_id = uid
        play_chime()

        self.sidebar.db_status.set_status(
            f"● GTR-{str(uid).zfill(4)} cargado", GREEN
        )

        self.profile_view.render(
            row, vehicles, activity, card_num,
            on_checkin=self._checkin,
            on_checkout=self._checkout,
        )

    # ══════════════════════════════════════════════════
    #  CHECK-IN / CHECK-OUT
    # ══════════════════════════════════════════════════
    def _checkin(self, uid: int, current_status: str) -> None:
        if current_status == "confirmed":
            messagebox.showinfo("Ya en Vault", "Este socio ya tiene un check-in activo.")
            return
        self._update_status(
            uid, "confirmed",
            f"✅ Check-In registrado para GTR-{str(uid).zfill(4)}.",
        )

    def _checkout(self, uid: int) -> None:
        self._update_status(
            uid, "completed",
            f"🚪 Check-Out registrado para GTR-{str(uid).zfill(4)}.",
        )

    def _update_status(self, uid: int, new_status: str, msg: str) -> None:
        def _do():
            try:
                reservation_service.update_status(uid, new_status)
                self.after(0, lambda: [
                    messagebox.showinfo("Actualizado", msg),
                    self._fetch_and_show(uid),
                ])
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        threading.Thread(target=_do, daemon=True).start()
