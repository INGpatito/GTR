"""
Parking GTR — Member Scanner Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana principal del scanner de socios.
Busca miembros por número de tarjeta, ID, o sensor.
Integra el sistema de estacionamiento con 24 espacios en 3 pisos.
"""

import json
import threading
import urllib.request
import urllib.error

import customtkinter as ctk
from tkinter import messagebox

from config.settings import print_startup_banner, ADMIN_API_KEY, API_BASE_URL
from config.theme import AMBER, DARK_BG, GREEN, RED, setup_ctk_theme
from core.crypto import generate_card_number
from services import reservation_service, member_service, vehicle_service
from services import parking_service
from ui.scanner.sidebar import ScannerSidebar
from ui.scanner.profile_view import ProfileView
from utils.sound import play_chime
from utils.mock_server import start_mock_server_background
from utils.esp32_controller import ESP32Controller

# Configurar tema global
setup_ctk_theme()


class MemberScanner(ctk.CTk):
    """Ventana principal del scanner de socios de Parking GTR."""

    # Polling interval for pending parking requests (ms)
    _PARKING_POLL_MS = 1000

    def __init__(self):
        super().__init__()
        print_startup_banner("Member Scanner")

        # Iniciar servidor mock provisional para sincronización con Android
        start_mock_server_background(3002)

        self.title("Parking GTR — Member Scanner")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        self.current_member_id: int | None = None
        self._show_spots_for_uid: int | None = None
        self._current_row = None
        self._current_vehicles = None
        self._current_activity = None
        self._current_card_num = None
        self._last_android_scan_ts = 0
        self._last_remote_scan_ts = 0
        self._last_pending_req_id = None

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

        # Iniciar controlador de hardware ESP32
        self.esp32 = ESP32Controller.get_instance()
        self.esp32.start()

        # Manejar cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start polling for pending parking requests
        self._start_parking_poll()

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
    def _fetch_and_show(self, member_id: int, show_spots: bool = False) -> None:
        """Carga datos del socio y renderiza su perfil."""
        self.sidebar.db_status.set_status("● Conectando...", AMBER)
        self.update()

        def _load():
            try:
                row = member_service.get_member_profile_by_user_id(member_id)
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

                # Get pending parking requests
                try:
                    pending = parking_service.get_pending_requests()
                except Exception:
                    pending = []

                # Get parking spots if requested
                spots = None
                if show_spots:
                    try:
                        spots = parking_service.get_all_spots()
                    except Exception:
                        spots = []

                self.after(0, lambda: self._render_profile(
                    row, vehicles, activity, card_num, pending, spots
                ))

            except Exception as exc:
                err_msg = str(exc)
                self.after(0, lambda: [
                    self.sidebar.db_status.set_status("● Error DB", RED),
                    messagebox.showerror("Error de base de datos", err_msg),
                ])

        threading.Thread(target=_load, daemon=True).start()

    def _render_profile(self, row, vehicles, activity, card_num,
                        pending_requests=None, parking_spots=None) -> None:
        """Renderiza el perfil y actualiza estado."""
        uid = row[0]
        full_name = row[1]
        self.current_member_id = uid
        self._current_row = row
        self._current_vehicles = vehicles
        self._current_activity = activity
        self._current_card_num = card_num
        play_chime()

        # Notify Android display via backend API
        self._notify_scan_event(full_name)

        self.sidebar.db_status.set_status(
            f"● GTR-{str(uid).zfill(4)} cargado", GREEN
        )

        self.profile_view.render(
            row, vehicles, activity, card_num,
            on_checkin=self._skip,
            on_checkout=self._checkout,
            on_close=self._close_profile,
            on_approve_request=self._approve_parking_request,
            on_reject_request=self._reject_parking_request,
            on_free_spot=self._free_spot,
            pending_requests=pending_requests,
            parking_spots=parking_spots,
        )

    def _notify_scan_event(self, member_name: str) -> None:
        """Sends scan event to backend and local mock server for Android display."""
        import time as _time
        from utils.mock_server import _latest_event_lock
        import utils.mock_server as _mock

        # 1. Escribir directamente en el mock server local (mismo proceso)
        with _latest_event_lock:
            _mock.latest_scan_event = {
                "member_name": member_name,
                "timestamp": int(_time.time() * 1000),
            }
        print(f"[SCAN-EVENT] Evento local registrado: {member_name}")

        # 2. También intentar notificar al backend remoto (si existe)
        def _send():
            try:
                url = f"{API_BASE_URL}/api/scan-event"
                data = json.dumps({"member_name": member_name}).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": ADMIN_API_KEY,
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    print(f"[SCAN-EVENT] Backend remoto notificado: {member_name} → {resp.status}")
            except Exception as e:
                # No es crítico si el backend remoto no está disponible
                pass

        threading.Thread(target=_send, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  SKIP / CHECK-OUT / CLOSE
    # ══════════════════════════════════════════════════
    def _skip(self, uid: int, current_status: str) -> None:
        """Skip — descarta el perfil actual sin acción de check-in."""
        self._close_profile()

    def _checkout(self, uid: int) -> None:
        """Check-Out — muestra el selector de spots para asignar o liberar."""
        self._fetch_and_show(uid, show_spots=True)

    def _free_spot(self, spot_id: int) -> None:
        """Libera manualmente un spot desde el mapa."""
        def _do():
            try:
                result = parking_service.free_spot(spot_id)
                if result:
                    self.esp32.open_gate(pin=2, duration_ms=2000)
                    self.after(0, lambda: [
                        messagebox.showinfo("Spot Liberado", "El espacio ha sido liberado."),
                        self._fetch_and_show(self.current_member_id, show_spots=True)
                        if self.current_member_id else None,
                    ])
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Error", "No se pudo liberar el espacio."
                    ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        import threading
        threading.Thread(target=_do, daemon=True).start()

    def _close_profile(self) -> None:
        """Cierra el perfil y vuelve a la pantalla de bienvenida."""
        self.current_member_id = None
        self._current_row = None
        self._current_vehicles = None
        self._current_activity = None
        self._current_card_num = None
        self._show_spots_for_uid = None
        self.sidebar.db_status.set_status("● Sin conexión", "#666666")
        self.profile_view.show_welcome()

    # ══════════════════════════════════════════════════
    #  PARKING REQUESTS — APPROVE / REJECT
    # ══════════════════════════════════════════════════
    def _approve_parking_request(self, request_id: int, request_type: str, spot_id: int = None) -> None:
        """Aprueba una solicitud de parking.

        check_in: Aprueba sin asignar spot — el usuario lo elige desde Android.
        check_out: Aprueba y libera los spots del usuario.
        heliport: Aprueba y reserva el helipuerto.
        """
        def _do():
            try:
                result = parking_service.approve_request(request_id, spot_id)
                if result:
                    self.esp32.open_gate(pin=2, duration_ms=2000)
                    type_labels = {
                        "check_in": "Ingreso aprobado. El socio elegirá su espacio desde la app.",
                        "check_out": "Retiro aprobado. Espacios liberados.",
                        "heliport": "Helipuerto reservado exitosamente.",
                    }
                    msg = type_labels.get(request_type, "Solicitud aprobada.")
                    self.after(0, lambda: [
                        messagebox.showinfo("Aprobado", msg),
                        self._fetch_and_show(self.current_member_id, show_spots=True)
                        if self.current_member_id else None,
                    ])
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Error", "No se pudo aprobar la solicitud."
                    ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        threading.Thread(target=_do, daemon=True).start()

    def _reject_parking_request(self, request_id: int) -> None:
        """Rechaza una solicitud de parking."""
        def _do():
            try:
                result = parking_service.reject_request(request_id)
                if result:
                    self.after(0, lambda: [
                        messagebox.showinfo("Rechazada", "Solicitud rechazada."),
                        self._fetch_and_show(self.current_member_id)
                        if self.current_member_id else None,
                    ])
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Error", "No se pudo rechazar la solicitud."
                    ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        threading.Thread(target=_do, daemon=True).start()

    # ══════════════════════════════════════════════════
    #  PARKING POLLING — Notificar cuando hay solicitudes
    # ══════════════════════════════════════════════════
    def _start_parking_poll(self) -> None:
        """Inicia polling periódico para solicitudes pendientes de parking."""
        self._check_parking_requests()

    def _check_parking_requests(self) -> None:
        """Verifica si hay solicitudes pendientes y actualiza la UI."""
        def _poll():
            try:
                pending = parking_service.get_pending_requests()
                if pending:
                    # Si hay solicitudes pendientes, obtener el ID y user_id de la primera
                    first_req = pending[0]
                    req_id = first_req[0]
                    req_user_id = first_req[1]

                    if req_id != self._last_pending_req_id:
                        self._last_pending_req_id = req_id
                        if self.current_member_id != req_user_id:
                            # Cargar y abrir de inmediato la información de este socio mostrando spots
                            self.after(0, lambda: self._fetch_and_show(req_user_id, show_spots=True))
                        else:
                            # Si ya está en pantalla, refrescar el panel con la info de la solicitud
                            self.after(0, lambda: self._refresh_with_pending(pending))
                else:
                    self._last_pending_req_id = None
            except Exception:
                pass  # DB no disponible

            try:
                import utils.mock_server as _mock
                with _mock._android_scan_lock:
                    latest_scan = _mock.latest_android_card_scan
                    
                if latest_scan and latest_scan["timestamp"] > self._last_android_scan_ts:
                    self._last_android_scan_ts = latest_scan["timestamp"]
                    scan_member_id = latest_scan["member_id"]
                    if self.current_member_id != scan_member_id:
                        self.after(0, lambda: self._fetch_and_show(scan_member_id))
            except Exception as e:
                print(f"[DEBUG] Error checking android scans: {e}")

            # Poll real Node.js backend for scan events
            try:
                import urllib.request
                import json
                from config.settings import API_BASE_URL
                url = f"{API_BASE_URL}/api/scan-event"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        if data.get("success") and data.get("event"):
                            event = data["event"]
                            if "member_id" in event and event["member_id"]:
                                ts = event.get("timestamp", 0)
                                if ts > self._last_remote_scan_ts:
                                    self._last_remote_scan_ts = ts
                                    scan_member_id = event["member_id"]
                                    if self.current_member_id != scan_member_id:
                                        self.after(0, lambda: self._fetch_and_show(scan_member_id))
            except Exception as e:
                pass

        threading.Thread(target=_poll, daemon=True).start()
        # Programar siguiente consulta rápida
        self.after(self._PARKING_POLL_MS, self._check_parking_requests)

    def _refresh_with_pending(self, pending_requests) -> None:
        """Re-renderiza el perfil actual con las solicitudes pendientes."""
        if not self._current_row:
            return

        # Don't re-render if we're on the welcome screen
        try:
            spots = parking_service.get_all_spots()
        except Exception:
            spots = None

        self.profile_view.render(
            self._current_row, self._current_vehicles,
            self._current_activity, self._current_card_num,
            on_checkin=self._skip,
            on_checkout=self._checkout,
            on_close=self._close_profile,
            on_approve_request=self._approve_parking_request,
            on_reject_request=self._reject_parking_request,
            on_free_spot=self._free_spot,
            pending_requests=pending_requests,
            parking_spots=spots,
        )

    # ══════════════════════════════════════════════════
    #  LEGACY CHECK-IN/OUT (for compatibility)
    # ══════════════════════════════════════════════════
    def _update_status(self, uid: int, new_status: str, msg: str) -> None:
        def _do():
            try:
                member_service.update_member_status_and_latest_reservation(uid, new_status)
                self.esp32.open_gate(pin=2, duration_ms=2000)
                self.after(0, lambda: [
                    messagebox.showinfo("Actualizado", msg),
                    self._fetch_and_show(uid),
                ])
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error DB", str(exc)))

        threading.Thread(target=_do, daemon=True).start()

    def _on_closing(self):
        """Manejador al cerrar la ventana principal del scanner."""
        self.esp32.stop()
        self.destroy()
