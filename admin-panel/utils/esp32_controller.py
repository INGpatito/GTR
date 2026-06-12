"""
Parking GTR — ESP32 Serial Controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gestiona la comunicación USB-Serial bidireccional con la placa ESP32.
Incluye reconexión automática y fallback a modo simulado (MOCK) si no hay hardware.
"""

import json
import time
import threading
import sys
import glob

try:
    import serial
except ImportError:
    serial = None


class ESP32Controller:
    """Clase thread-safe para comunicarse con la ESP32 vía USB-Serial."""

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
        
        self.write_lock = threading.Lock()
        self.thread = None

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
            # Encontrar puertos ttyUSB o ttyACM
            ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.usb*')
        else:
            ports = []
            
        available_ports = []
        for p in ports:
            try:
                # Comprobar si se puede abrir el puerto de forma rápida
                if serial:
                    s = serial.Serial(p)
                    s.close()
                    available_ports.append(p)
            except (OSError, Exception):
                pass
        return available_ports

    def _connection_loop(self):
        """Bucle de conexión y reconexión automática en segundo plano."""
        print("[ESP32] Iniciando bucle de conexión de hardware...")
        while self.running:
            if not self.connected:
                if serial is None:
                    if self.mock_mode:
                        print("[ESP32] Pyserial no instalado. Ejecutando en modo SIMULADO.")
                        self.mock_mode = True
                        time.sleep(5)
                        continue
                
                ports = self._find_serial_ports()
                if ports:
                    self.port = ports[0]
                    print(f"[ESP32] Intentando conectar al puerto: {self.port}...")
                    try:
                        self.ser = serial.Serial(
                            port=self.port,
                            baudrate=self.baudrate,
                            timeout=1.0,
                            write_timeout=2.0
                        )
                        # Dar tiempo a la ESP32 para reiniciar/estabilizar conexión
                        time.sleep(2)
                        
                        self.connected = True
                        self.mock_mode = False
                        print(f"[ESP32] ¡Conexión exitosa en {self.port}!")
                        
                        # Vaciar buffers
                        self.ser.reset_input_buffer()
                        self.ser.reset_output_buffer()
                    except Exception as e:
                        print(f"[ESP32] Error abriendo puerto {self.port}: {e}")
                        self.connected = False
                        self.ser = None
                else:
                    if not self.mock_mode:
                        print("[ESP32] No se detectó ninguna placa ESP32 por USB. Modo SIMULADO activo.")
                        self.mock_mode = True
                    
            # Si estamos conectados, escuchar respuestas entrantes
            if self.connected and self.ser:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self._handle_response(line)
                except Exception as e:
                    print(f"[ESP32] Conexión perdida: {e}")
                    self.connected = False
                    if self.ser:
                        try:
                            self.ser.close()
                        except Exception:
                            pass
                        self.ser = None
            
            time.sleep(0.1 if self.connected else 3.0)

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
            # Respuesta no JSON, loguear como texto plano
            print(f"[ESP32 TXT] -> {line}")

    def send_command(self, cmd_dict):
        """Envía un comando JSON de forma segura y thread-safe."""
        payload = json.dumps(cmd_dict) + "\n"
        
        if self.mock_mode or not self.connected or not self.ser:
            # Imular comportamiento físico
            threading.Thread(
                target=self._simulate_physical_response,
                args=(cmd_dict,),
                daemon=True
            ).start()
            return True

        with self.write_lock:
            try:
                self.ser.write(payload.encode('utf-8'))
                self.ser.flush()
                print(f"[ESP32 CMD SEND] <- {payload.strip()}")
                return True
            except Exception as e:
                print(f"[ESP32 CMD ERROR] Fallo al enviar comando: {e}")
                self.connected = False
                return False

    def open_gate(self, pin=2, duration_ms=2000):
        """Instrucción para abrir físicamente el portón/pluma de parking."""
        cmd = {
            "command": "open_gate",
            "pin": pin,
            "duration": duration_ms
        }
        return self.send_command(cmd)

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
