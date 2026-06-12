import http.server
import json
import time
import threading
import re

# Guardamos el último evento de escaneo en memoria (compartido e hilo seguro)
_latest_event_lock = threading.Lock()
latest_scan_event = None

# Parking requests en memoria (para modo mock sin DB)
_parking_lock = threading.Lock()
_pending_parking_requests = []
_next_request_id = 1


class GtrMockServer(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciamos los logs de peticiones HTTP en consola para no ensuciar la terminal del scanner
        pass

    def end_headers(self):
        # Agregamos cabeceras CORS para permitir cualquier origen (CORS universal)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length else {}

    def do_GET(self):
        global latest_scan_event
        if self.path == "/api/health":
            self._send_json({"success": True, "status": "ok"})

        elif self.path == "/api/scan-event":
            with _latest_event_lock:
                if latest_scan_event:
                    resp = {"success": True, "event": latest_scan_event}
                else:
                    resp = {"success": True, "event": None}
            self._send_json(resp)

        elif self.path == "/api/parking/request/pending":
            self._handle_get_pending_requests()

        elif self.path.startswith("/api/parking/spots"):
            self._handle_get_spots()

        elif self.path.startswith("/api/parking/request/") and self.path.endswith("/status"):
            self._handle_get_request_status()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global latest_scan_event
        if self.path == "/api/scan-event":
            try:
                data = self._read_body()
                member_name = data.get("member_name", "")

                with _latest_event_lock:
                    latest_scan_event = {
                        "member_name": member_name,
                        "timestamp": int(time.time() * 1000)
                    }

                print(f"[MOCK-SERVER] Evento de escaneo recibido: {member_name}")
                self._send_json({"success": True})
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))

        elif self.path == "/api/scan-event/card":
            self._handle_card_scan()

        elif self.path == "/api/parking/request":
            self._handle_create_parking_request()

        elif self.path.startswith("/api/parking/checkout/"):
            self._handle_checkout_spot()

        else:
            self.send_response(404)
            self.end_headers()

    def do_PATCH(self):
        # Match /api/parking/request/:id/approve or /api/parking/request/:id/reject
        match_approve = re.match(r'^/api/parking/request/(\d+)/approve$', self.path)
        match_reject = re.match(r'^/api/parking/request/(\d+)/reject$', self.path)

        if match_approve:
            self._handle_approve_request(int(match_approve.group(1)))
        elif match_reject:
            self._handle_reject_request(int(match_reject.group(1)))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        global latest_scan_event
        if self.path == "/api/scan-event":
            with _latest_event_lock:
                latest_scan_event = None

            self._send_json({"success": True})
        else:
            self.send_response(404)
            self.end_headers()

    # ── Card scan handler ──────────────────────────────
    def _handle_card_scan(self):
        try:
            data = self._read_body()
            card_number = data.get("card_number", "")
            clean_card = card_number.replace(" ", "").replace("-", "")

            member_name = None
            member_id = None
            try:
                from services import member_service
                from core.crypto import generate_card_number
                ids = member_service.get_all_member_ids()
                for mid in ids:
                    generated = generate_card_number(mid).replace(" ", "")
                    if generated == clean_card:
                        row = member_service.get_member_profile_by_user_id(mid)
                        if row:
                            member_name = row[1]
                            member_id = row[0]
                        break
            except Exception as db_err:
                print(f"[MOCK-SERVER] Error accediendo a DB para tarjeta: {db_err}")

            if not member_name:
                member_name = f"Socio Simulado ({clean_card[-4:] if len(clean_card) >= 4 else 'GTR'})"

            global latest_scan_event
            with _latest_event_lock:
                latest_scan_event = {
                    "member_name": member_name,
                    "timestamp": int(time.time() * 1000)
                }

            print(f"[MOCK-SERVER] Evento via tarjeta recibido: {member_name}")

            resp = {"success": True, "member_name": member_name}
            if member_id:
                resp["member_id"] = member_id
                # Also fetch vehicles
                try:
                    from services import member_service as _ms
                    vehicles = _ms.get_member_vehicles(member_id)
                    resp["vehicles"] = [
                        {
                            "id": v[0], "nickname": v[1], "vehicle_type": v[2],
                            "brand": v[3], "model": v[4], "year": v[5],
                            "color": v[6], "plate": v[7], "is_primary": v[8]
                        }
                        for v in vehicles
                    ]
                except Exception:
                    resp["vehicles"] = []

            self._send_json(resp)
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    # ── Parking request handlers ───────────────────────
    def _handle_create_parking_request(self):
        global _next_request_id
        try:
            data = self._read_body()
            user_id = data.get("user_id")
            vehicle_id = data.get("vehicle_id")
            request_type = data.get("request_type")

            if not user_id or not request_type:
                self._send_json({"success": False, "errors": ["user_id y request_type requeridos"]}, 400)
                return

            # Try DB first
            try:
                from services import parking_service
                result = parking_service.create_request(user_id, vehicle_id, request_type)
                if result:
                    req_data = {
                        "id": result[0], "user_id": result[1], "vehicle_id": result[2],
                        "request_type": result[3], "status": result[4]
                    }
                    print(f"[MOCK-SERVER] Parking request (DB): user={user_id}, type={request_type}")
                    self._send_json({"success": True, "request": req_data})
                    return
            except Exception as db_err:
                print(f"[MOCK-SERVER] DB unavailable for parking request, using memory: {db_err}")

            # Fallback: in-memory
            with _parking_lock:
                req = {
                    "id": _next_request_id,
                    "user_id": user_id,
                    "vehicle_id": vehicle_id,
                    "request_type": request_type,
                    "status": "pending",
                    "created_at": time.time()
                }
                # Remove previous pending from same user
                _pending_parking_requests[:] = [
                    r for r in _pending_parking_requests
                    if not (r["user_id"] == user_id and r["status"] == "pending")
                ]
                _pending_parking_requests.append(req)
                _next_request_id += 1

            print(f"[MOCK-SERVER] Parking request (memory): user={user_id}, type={request_type}")
            self._send_json({"success": True, "request": req})
        except Exception as e:
            self._send_json({"success": False, "errors": [str(e)]}, 400)

    def _handle_get_pending_requests(self):
        # Try DB first
        try:
            from services import parking_service
            rows = parking_service.get_pending_requests()
            requests = []
            for r in rows:
                requests.append({
                    "id": r[0], "user_id": r[1], "vehicle_id": r[2],
                    "request_type": r[3], "status": r[4],
                    "created_at": str(r[5]) if r[5] else None,
                    "full_name": r[6], "email": r[7],
                    "vehicle_nickname": r[8], "brand": r[9],
                    "model": r[10], "plate": r[11],
                    "vehicle_type": r[12]
                })
            self._send_json({"success": True, "requests": requests})
            return
        except Exception:
            pass

        # Fallback: in-memory
        with _parking_lock:
            pending = [r for r in _pending_parking_requests if r["status"] == "pending"]
        self._send_json({"success": True, "requests": pending})

    def _handle_get_request_status(self):
        # Extract user ID from path like /api/parking/request/123/status
        match = re.match(r'^/api/parking/request/(\d+)/status$', self.path)
        if not match:
            self._send_json({"success": False}, 400)
            return

        user_id = int(match.group(1))

        try:
            from services import parking_service
            row = parking_service.get_request_status(user_id)
            if row:
                req = {
                    "id": row[0], "request_type": row[1], "status": row[2],
                    "spot_id": row[3], "created_at": str(row[4]) if row[4] else None
                }
                self._send_json({"success": True, "request": req})
            else:
                self._send_json({"success": True, "request": None})
            return
        except Exception:
            pass

        self._send_json({"success": True, "request": None})

    def _handle_approve_request(self, request_id):
        data = self._read_body()
        spot_id = data.get("spot_id")

        try:
            from services import parking_service
            result = parking_service.approve_request(request_id, spot_id)
            if result:
                print(f"[MOCK-SERVER] Parking request {request_id} approved")
                self._send_json({"success": True})
            else:
                self._send_json({"success": False, "errors": ["No se pudo aprobar"]}, 400)
            return
        except Exception as e:
            print(f"[MOCK-SERVER] DB error approving: {e}")

        # Fallback: in-memory
        with _parking_lock:
            for r in _pending_parking_requests:
                if r["id"] == request_id and r["status"] == "pending":
                    r["status"] = "approved"
                    r["spot_id"] = spot_id
                    self._send_json({"success": True})
                    return
        self._send_json({"success": False, "errors": ["Not found"]}, 404)

    def _handle_reject_request(self, request_id):
        try:
            from services import parking_service
            result = parking_service.reject_request(request_id)
            if result:
                print(f"[MOCK-SERVER] Parking request {request_id} rejected")
                self._send_json({"success": True})
            else:
                self._send_json({"success": False, "errors": ["Not found"]}, 404)
            return
        except Exception:
            pass

        # Fallback: in-memory
        with _parking_lock:
            for r in _pending_parking_requests:
                if r["id"] == request_id and r["status"] == "pending":
                    r["status"] = "rejected"
                    self._send_json({"success": True})
                    return
        self._send_json({"success": False, "errors": ["Not found"]}, 404)

    def _handle_get_spots(self):
        # Try DB
        try:
            from services import parking_service
            floor_match = re.match(r'^/api/parking/spots/(\d+)$', self.path)
            if floor_match:
                spots = parking_service.get_spots_by_floor(int(floor_match.group(1)))
            else:
                spots = parking_service.get_all_spots()
            result = []
            for s in spots:
                result.append({
                    "id": s[0], "spot_number": s[1], "floor": s[2],
                    "spot_label": s[3], "status": s[4],
                    "occupied_by_user_id": s[5], "occupied_by_vehicle_id": s[6],
                    "occupied_at": str(s[7]) if s[7] else None,
                    "user_name": s[8], "vehicle_nickname": s[9],
                    "brand": s[10], "model": s[11], "plate": s[12]
                })
            self._send_json({"success": True, "spots": result})
            return
        except Exception as e:
            print(f"[MOCK-SERVER] DB error getting spots: {e}")

        # Fallback: empty
        self._send_json({"success": True, "spots": []})

    def _handle_checkout_spot(self):
        match = re.match(r'^/api/parking/checkout/(\d+)$', self.path)
        if not match:
            self._send_json({"success": False}, 400)
            return

        spot_id = int(match.group(1))
        try:
            from services import parking_service
            parking_service.free_spot(spot_id)
            print(f"[MOCK-SERVER] Spot {spot_id} freed")
            self._send_json({"success": True})
            return
        except Exception as e:
            print(f"[MOCK-SERVER] DB error freeing spot: {e}")
        self._send_json({"success": False}, 500)


def start_mock_server_background(port: int = 3000):
    """Inicia el servidor mock en segundo plano. Si el puerto ya está en uso,

    asume que el servidor real de Node.js está corriendo y continúa sin problemas.
    """
    def _run():
        try:
            server = http.server.HTTPServer(("0.0.0.0", port), GtrMockServer)
            print(f"[MOCK-SERVER] Servidor provisional iniciado en http://0.0.0.0:{port}")
            print(f"[MOCK-SERVER] Listo para sincronizar eventos con la App Android en tiempo real.")
            server.serve_forever()
        except OSError as e:
            if e.errno == 98 or "Address already in use" in str(e):
                print(f"[INFO] Puerto {port} ya está en uso. Asumiendo que el servidor Backend real (Node.js) ya está corriendo.")
            else:
                print(f"[WARNING] No se pudo iniciar el servidor provisional en puerto {port}: {e}")
        except Exception as e:
            print(f"[WARNING] Error inesperado en el servidor provisional: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
