import http.server
import json
import time
import threading

# Guardamos el último evento de escaneo en memoria (compartido e hilo seguro)
_latest_event_lock = threading.Lock()
latest_scan_event = None


class GtrMockServer(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciamos los logs de peticiones HTTP en consola para no ensuciar la terminal del scanner
        pass

    def end_headers(self):
        # Agregamos cabeceras CORS para permitir cualquier origen (CORS universal)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        global latest_scan_event
        if self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "status": "ok"}).encode("utf-8"))

        elif self.path == "/api/scan-event":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            with _latest_event_lock:
                if latest_scan_event:
                    resp = {
                        "success": True,
                        "event": latest_scan_event
                    }
                else:
                    resp = {
                        "success": True,
                        "event": None
                    }
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global latest_scan_event
        if self.path == "/api/scan-event":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                member_name = data.get("member_name", "")
                
                with _latest_event_lock:
                    latest_scan_event = {
                        "member_name": member_name,
                        "timestamp": int(time.time() * 1000)
                    }
                
                print(f"[MOCK-SERVER] Evento de escaneo recibido: {member_name}")
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        global latest_scan_event
        if self.path == "/api/scan-event":
            with _latest_event_lock:
                latest_scan_event = None
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


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
