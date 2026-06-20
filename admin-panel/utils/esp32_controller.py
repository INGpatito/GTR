"""
Parking GTR — ESP32 Serial & WiFi Controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gestiona la comunicación USB-Serial bidireccional y WiFi con la placa ESP32.
Prioriza la conexión WiFi por HTTP si está disponible, con fallback automático a USB-Serial
y modo simulado (MOCK) si no hay hardware conectado.
"""

import os
import json
import time
import threading
import sys
import glob
import requests

try:
    import serial
except ImportError:
    serial = None


class ESP32Controller:
    """Clase thread-safe para comunicarse con la ESP32 vía WiFi (HTTP) o USB-Serial."""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Retorna una instancia única global (Singleton)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        # Evitar inicialización doble
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._initialized = True
        self.port = None
        self.baudrate = 115200
        self.ser = None
        self.running = False
        self.connected = False
        self.mock_mode = True
        
        # Dirección IP de la ESP32 (cargada de .env u obtenida por registro dinámico)
        self.wifi_ip = os.getenv("ESP32_IP")
        if self.wifi_ip:
            print(f"[ESP32] IP de WiFi pre-configurada desde .env: {self.wifi_ip}")
            
        self.write_lock = threading.Lock()
        self.thread = None

    def set_wifi_ip(self, ip):
        """Asigna la dirección IP de la ESP32 de forma dinámica."""
        self.wifi_ip = ip.strip()
        print(f"[ESP32] IP de WiFi configurada dinámicamente: {self.wifi_ip}")

    def start(self):
        """Inicia el hilo de monitoreo y conexión serial."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Cierra el hilo y la conexión serial."""
        self.running = False
        self.connected = False
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
        print("[ESP32] Conexión cerrada de forma limpia.")

    def _find_serial_ports(self):
        """Encuentra puertos seriales disponibles en el sistema."""
        if sys.platform.startswith('win'):
            ports = [f'COM{i}' for i in range(1, 256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.usb*')
        else:
            ports = []
            
        available_ports = []
        for p in ports:
            try:
                if serial:
                    s = serial.Serial(p)
                    s.close()
                    available_ports.append(p)
            except (OSError, Exception):
                pass
        return available_ports

    def _check_wifi_alive(self):
        """Verifica si la ESP32 responde por WiFi (HTTP heartbeat)."""
        if not self.wifi_ip:
            return False
        try:
            r = requests.get(f"http://{self.wifi_ip}/api/heartbeat", timeout=2.5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        return False

    def _connection_loop(self):
        """Bucle de conexión y reconexión automática (WiFi + Serial) en segundo plano."""
        print("[ESP32] Iniciando bucle de monitoreo (WiFi + Serial)...")
        wifi_check_counter = 0
        while self.running:
            # ── Canal 1: Verificar conexión WiFi ──
            # Cada ~5 iteraciones (~15s cuando desconectado) hacer health-check WiFi
            wifi_check_counter += 1
            if self.wifi_ip and (wifi_check_counter >= 5 or not self.connected):
                wifi_check_counter = 0
                wifi_alive = self._check_wifi_alive()
                if wifi_alive and not self.connected:
                    self.connected = True
                    self.mock_mode = False
                    print(f"[ESP32] ¡Conexión WiFi verificada! IP: {self.wifi_ip}")
                elif not wifi_alive and self.connected and not self.ser:
                    # Solo marcar desconectado si no hay serial activo
                    print(f"[ESP32] WiFi sin respuesta desde {self.wifi_ip}. Reintentando...")
                    self.connected = False

            # ── Canal 2: Conexión Serial ──
            if not self.connected or not self.ser:
                if serial is None:
                    if self.mock_mode and not self.wifi_ip:
                        print("[ESP32] Pyserial no instalado y no hay IP configurada. Ejecutando en modo SIMULADO.")
                        time.sleep(5)
                        continue
                elif not self.ser:
                    ports = self._find_serial_ports()
                    if ports:
                        self.port = ports[0]
                        print(f"[ESP32] Puerto serial encontrado: {self.port}. Intentando conectar...")
                        try:
                            self.ser = serial.Serial(
                                port=self.port,
                                baudrate=self.baudrate,
                                timeout=1.0,
                                write_timeout=2.0
                            )
                            time.sleep(2)  # Reinicio físico de ESP32
                            self.connected = True
                            self.mock_mode = False
                            print(f"[ESP32] ¡Conexión serial exitosa en {self.port}!")
                            
                            self.ser.reset_input_buffer()
                            self.ser.reset_output_buffer()
                        except Exception as e:
                            print(f"[ESP32] Error abriendo puerto serial {self.port}: {e}")
                            self.ser = None
                    elif not self.connected and not self.wifi_ip:
                        if not self.mock_mode:
                            print("[ESP32] Sin puerto serial y sin WiFi. Modo SIMULADO activo.")
                            self.mock_mode = True

            # ── Leer datos del Serial si está activo ──
            if self.ser:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self._handle_response(line)
                except Exception as e:
                    print(f"[ESP32] Conexión serial perdida: {e}")
                    self.connected = False if not self.wifi_ip else self.connected
                    if self.ser:
                        try:
                            self.ser.close()
                        except Exception:
                            pass
                        self.ser = None
            
            time.sleep(0.1 if self.connected else 3.0)

    def get_status(self):
        """Retorna un diccionario con el estado actual del controlador para diagnóstico."""
        return {
            "connected": self.connected,
            "mock_mode": self.mock_mode,
            "wifi_ip": self.wifi_ip,
            "serial_port": self.port if self.ser else None,
            "serial_connected": self.ser is not None,
        }

    def _handle_response(self, line):
        """Procesa y parsea las respuestas recibidas de la ESP32."""
        print(f"[ESP32 RAW] -> {line}")
        try:
            data = json.loads(line)
            status = data.get("status")
            action = data.get("action")
            
            if status == "executing" and action == "open_gate":
                print(f"[HARDWARE] Barrera física activándose (Pin {data.get('pin')}) por {data.get('duration')}ms...")
            elif status == "success" and action == "close_gate":
                print(f"[HARDWARE] Barrera física desactivada (Pin {data.get('pin')}). Portón cerrado.")
            elif status == "ready":
                print(f"[HARDWARE] Placa ESP32 inicializada correctamente: {data.get('device')}")
            elif status == "pong":
                print("[HARDWARE] Latencia OK (Pong recibido de ESP32).")
        except Exception:
            print(f"[ESP32 TXT] -> {line}")

    def send_command(self, cmd_dict):
        """Envía un comando. Intenta WiFi y hace fallback a Serial y luego a Mock."""
        cmd = cmd_dict.get("command")
        
        # --- Canal 1: WiFi (HTTP) ---
        if self.wifi_ip:
            try:
                if cmd == "open_gate":
                    pin = cmd_dict.get("pin", 2)
                    dur = cmd_dict.get("duration", 2000)
                    url = f"http://{self.wifi_ip}/api/gate?pin={pin}&duration={dur}"
                    print(f"[ESP32 HTTP GET] <- {url}")
                    r = requests.get(url, timeout=2.5)
                    if r.status_code == 200:
                        print(f"[ESP32 HTTP RES] -> {r.text.strip()}")
                        return True
                elif cmd == "ping":
                    url = f"http://{self.wifi_ip}/api/status"
                    print(f"[ESP32 HTTP GET] <- {url}")
                    r = requests.get(url, timeout=2.5)
                    if r.status_code == 200:
                        print(f"[ESP32 HTTP RES] -> {r.text.strip()}")
                        return True
            except Exception as wifi_err:
                print(f"[ESP32 WiFi ERROR] Fallo al conectar por WiFi: {wifi_err}. Reintentando por Serial...")

        # --- Canal 2: USB-Serial ---
        if self.connected and self.ser:
            payload = json.dumps(cmd_dict) + "\n"
            with self.write_lock:
                try:
                    self.ser.write(payload.encode('utf-8'))
                    self.ser.flush()
                    print(f"[ESP32 SERIAL CMD] <- {payload.strip()}")
                    return True
                except Exception as e:
                    print(f"[ESP32 SERIAL ERROR] Fallo al enviar comando por cable: {e}")
                    self.connected = False

        # --- Canal 3: Mock/Simulado ---
        threading.Thread(
            target=self._simulate_physical_response,
            args=(cmd_dict,),
            daemon=True
        ).start()
        return True

    def open_gate(self, pin=2, duration_ms=2000):
        """Instrucción para abrir físicamente el portón/pluma de parking."""
        cmd = {
            "command": "open_gate",
            "pin": pin,
            "duration": duration_ms
        }
        return self.send_command(cmd)

    def set_led(self, state):
        """Enciende o apaga el LED de prueba (state = 1 o 0)."""
        state_val = 1 if state else 0
        
        # --- Canal 1: WiFi ---
        if self.wifi_ip:
            try:
                url = f"http://{self.wifi_ip}/api/led?state={state_val}"
                print(f"[ESP32 HTTP GET] <- {url}")
                r = requests.get(url, timeout=2.5)
                if r.status_code == 200:
                    print(f"[ESP32 HTTP RES] -> {r.text.strip()}")
                    return True
            except Exception as wifi_err:
                print(f"[ESP32 WiFi ERROR] Fallo al apagar/prender LED: {wifi_err}. Reintentando por Serial...")

        # --- Canal 2: Serial ---
        if self.connected and self.ser:
            payload = f"LED:{state_val}\n"
            with self.write_lock:
                try:
                    self.ser.write(payload.encode('utf-8'))
                    self.ser.flush()
                    print(f"[ESP32 SERIAL CMD] <- {payload.strip()}")
                    return True
                except Exception as e:
                    print(f"[ESP32 SERIAL ERROR] Fallo al cambiar LED por cable: {e}")
                    self.connected = False

        # --- Canal 3: Mock ---
        print(f"[SIMULADO] [HARDWARE] LED de prueba (GPIO 2) cambiado a estado: {state_val}")
        return True

    def ping(self):
        """Verifica la conectividad de la placa."""
        return self.send_command({"command": "ping"})

    def _simulate_physical_response(self, cmd_dict):
        """Simulador del comportamiento físico de la ESP32 si no está conectada."""
        cmd = cmd_dict.get("command")
        if cmd == "open_gate":
            pin = cmd_dict.get("pin", 2)
            duration = cmd_dict.get("duration", 2000)
            
            print(f"[SIMULADO] [ESP32] <- {json.dumps(cmd_dict)}")
            print(f"[SIMULADO] [HARDWARE] Barrera física abriéndose (Pin {pin}) por {duration}ms...")
            time.sleep(duration / 1000.0)
            print(f"[SIMULADO] [HARDWARE] Barrera física cerrada (Pin {pin}).")
        elif cmd == "ping":
            print(f"[SIMULADO] [ESP32] <- {json.dumps(cmd_dict)}")
            print("[SIMULADO] [HARDWARE] Latencia OK (Pong recibido de ESP32).")
