#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* ssid = "GTR ENTRADA";
const char* password = "12345678";

WebServer server(80);

// --- OBJETOS SERVO ---
Servo servoEntrada;
Servo servoSalida;

// --- CONFIGURACIÓN DE PINES ---
const int pinServoEntrada  = 18; 
const int pinServoSalida   = 19; 

// Sensores de Entrada
const int pinIREntradaAbrir   = 16; // IR Externo (Abre entrada)
const int pinTriggerEntrada   = 4;  // Ultrasonido Interno - Trigger
const int pinEchoEntrada      = 17; // Ultrasonido Interno - Echo (Cierra entrada)

// Sensores de Salida
const int pinTriggerSalida    = 5;  // Ultrasonido Interno - Trigger (Abre salida)
const int pinEchoSalida       = 12; // Ultrasonido Interno - Echo
const int pinIRSalidaCerrar   = 23; // IR Externo (Cierra salida)

// --- 📐 CONFIGURACIÓN DE ÁNGULOS INDEPENDIENTES ---
const int anguloEntradaCerrado = 180;   // Entrada abajo
const int anguloEntradaAbierto = 90;  // Entrada arriba

const int anguloSalidaCerrado  = 180;   // Salida abajo
const int anguloSalidaAbierto  = 90;  // Salida arriba

// --- VARIABLES DE ESTADO ---
bool entradaAbierta = false;
bool entradaPasando = false;

bool salidaAbierta = false;
bool salidaPasando = false;

unsigned long ultimoEscaneo = 0;
const int distanciaCorte = 10; // Distancia límite en cm para los ultrasónicos (ej: menos de 10cm = coche detectado)

// Función auxiliar para leer la distancia de un sensor ultrasónico
long obtenerDistancia(int triggerPin, int echoPin) {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  
  long duracion = pulseIn(echoPin, HIGH, 30000); // Timeout de 30ms para evitar trabas
  long distancia = duracion * 0.034 / 2;
  
  if (distancia == 0) return 999; // Si da 0 es porque está fuera de rango, devolvemos un valor alto
  return distancia;
}

// --- INTERFAZ WEB PREMIUM INTACTA ---
String paginaHTML = R"rawliteral(
<!DOCTYPE html>
<html lang="es">
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta charset='UTF-8'>
    <title>Control de Acceso Dual</title>
    <style>
        :root {
            --color-bg: #050505; --color-gold: #d4af37; --color-gold-soft: #f1d788;
            --color-text: #f8f5ed; --color-muted: #c8bc98; --color-glass: rgba(18, 18, 18, 0.56);
            --color-line: rgba(212, 175, 55, 0.42); --shadow-soft: 0 20px 45px rgba(0, 0, 0, 0.5);
            --shadow-gold: 0 0 35px rgba(212, 175, 55, 0.28); --radius-lg: 24px; --radius-md: 16px;
            --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; background-color: var(--color-bg); color: var(--color-text); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { background: var(--color-glass); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid var(--color-line); padding: 40px 20px; border-radius: var(--radius-lg); width: 100%; max-width: 500px; text-align: center; box-shadow: var(--shadow-soft), var(--shadow-gold); }
        h1 { font-size: 26px; font-weight: 300; letter-spacing: 2px; color: var(--color-gold-soft); margin-bottom: 5px; text-transform: uppercase; }
        .subtitle { color: var(--color-muted); font-size: 12px; margin-bottom: 30px; letter-spacing: 1px; }
        .grid-accesos { display: flex; gap: 20px; justify-content: space-between; }
        .seccion { flex: 1; background: rgba(255,255,255,0.03); padding: 20px 15px; border-radius: var(--radius-md); border: 1px solid rgba(212, 175, 55, 0.15); }
        .seccion h2 { font-size: 16px; color: var(--color-text); margin-bottom: 15px; letter-spacing: 1px; }
        .btn { display: block; width: 100%; background: transparent; border: 1px solid var(--color-gold); color: var(--color-gold); padding: 14px; font-size: 13px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; border-radius: var(--radius-md); cursor: pointer; margin-bottom: 12px; transition: all 0.4s var(--ease-out-expo); outline: none; }
        .btn:last-child { margin-bottom: 0; }
        .btn-abrir:active, .btn-abrir.activo { background-color: var(--color-gold); color: var(--color-bg); box-shadow: 0 0 15px var(--color-gold); transform: scale(0.96); }
        .btn-cerrar { border-color: var(--color-muted); color: var(--color-muted); }
        .btn-cerrar:active, .btn-cerrar.activo { background-color: var(--color-text); color: var(--color-bg); border-color: var(--color-text); box-shadow: 0 0 15px rgba(255,255,255,0.3); transform: scale(0.96); }
    </style>
    <script>
        function enviarComando(ruta, boton) {
            boton.classList.add('activo');
            setTimeout(() => boton.classList.remove('activo'), 200);
            var xhttp = new XMLHttpRequest();
            xhttp.open("GET", "/" + ruta, true);
            xhttp.send();
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>CONTROL DE ACCESOS</h1>
        <div class="subtitle">ESTACIÓN ACCESO AUTOMATIZADO</div>
        
        <div class="grid-accesos">
            <div class="seccion">
                <h2>ENTRADA</h2>
                <button class="btn btn-abrir" onclick="enviarComando('e_abrir', this)">ABRIR</button>
                <button class="btn btn-cerrar" onclick="enviarComando('e_cerrar', this)">CERRAR</button>
            </div>
            
            <div class="seccion">
                <h2>SALIDA</h2>
                <button class="btn btn-abrir" onclick="enviarComando('s_abrir', this)">ABRIR</button>
                <button class="btn btn-cerrar" onclick="enviarComando('s_cerrar', this)">CERRAR</button>
            </div>
        </div>
    </div>
</body>
</html>
)rawliteral";

void setup() {
  Serial.begin(115200);

  // Pines Sensores IR
  pinMode(pinIREntradaAbrir, INPUT);
  pinMode(pinIRSalidaCerrar, INPUT);

  // Pines Ultrasónico Entrada
  pinMode(pinTriggerEntrada, OUTPUT);
  pinMode(pinEchoEntrada, INPUT);

  // Pines Ultrasónico Salida
  pinMode(pinTriggerSalida, OUTPUT);
  pinMode(pinEchoSalida, INPUT);

  // Inicializar servos en posición cerrada con sus ángulos independientes
  servoEntrada.attach(pinServoEntrada);
  servoSalida.attach(pinServoSalida);
  servoEntrada.write(anguloEntradaCerrado);
  servoSalida.write(anguloSalidaCerrado);

  WiFi.softAP(ssid, password);
  Serial.print("Servidor en línea. Dirección IP: ");
  Serial.println(WiFi.softAPIP());

  // --- RUTAS WEB ---
  server.on("/", []() { server.send(200, "text/html", paginaHTML); });
  
  server.on("/e_abrir", []() { servoEntrada.write(anguloEntradaAbierto); entradaAbierta = true; server.send(200, "text/plain", "OK"); });
  server.on("/e_cerrar", []() { servoEntrada.write(anguloEntradaCerrado); entradaAbierta = false; entradaPasando = false; server.send(200, "text/plain", "OK"); });
  
  server.on("/s_abrir", []() { servoSalida.write(anguloSalidaAbierto); salidaAbierta = true; server.send(200, "text/plain", "OK"); });
  server.on("/s_cerrar", []() { servoSalida.write(anguloSalidaCerrado); salidaAbierta = false; salidaPasando = false; server.send(200, "text/plain", "OK"); });

  server.begin();
}

void loop() {
  server.handleClient(); // Atiende la web sin retrasos

  // Lógica de sensores cada 80ms
  if (millis() - ultimoEscaneo > 80) {
    ultimoEscaneo = millis();

    // ==========================================
    // 🚗 CONTROL AUTOMÁTICO DE ENTRADA
    // ==========================================
    if (!entradaAbierta) {
      // Abre con el IR Externo
      if (digitalRead(pinIREntradaAbrir) == LOW) { 
        Serial.println("Sensor IR Ext: Carro detectado al llegar. Abriendo entrada...");
        servoEntrada.write(anguloEntradaAbierto);
        entradaAbierta = true;
      }
    } else {
      // Cierra con el Ultrasónico Interno
      long distEntrada = obtenerDistancia(pinTriggerEntrada, pinEchoEntrada);
      if (distEntrada < distanciaCorte) {
        entradaPasando = true; // El coche está pasando frente al ultrasónico
      } 
      else if (distEntrada >= distanciaCorte && entradaPasando) {
        Serial.println("Sensor Ultra Int: Carro ingresó por completo. Cerrando entrada...");
        delay(800); // Tiempo de cortesía trasera
        servoEntrada.write(anguloEntradaCerrado);
        entradaAbierta = false;
        entradaPasando = false;
      }
    }

    // ==========================================
    // 🚙 CONTROL AUTOMÁTICO DE SALIDA
    // ==========================================
    if (!salidaAbierta) {
      // Abre con el Ultrasónico Interno
      long distSalida = obtenerDistancia(pinTriggerSalida, pinEchoSalida);
      if (distSalida < distanciaCorte) {
        Serial.println("Sensor Ultra Int: Carro aproximándose a la salida. Abriendo...");
        servoSalida.write(anguloSalidaAbierto);
        salidaAbierta = true;
      }
    } else {
      // Cierra con el IR Externo
      if (digitalRead(pinIRSalidaCerrar) == LOW) {
        salidaPasando = true; // El coche está obstruyendo el IR externo de salida
      } 
      else if (digitalRead(pinIRSalidaCerrar) == HIGH && salidaPasando) {
        Serial.println("Sensor IR Ext: Carro salió por completo al exterior. Cerrando...");
        delay(800); // Tiempo de cortesía trasera
        servoSalida.write(anguloSalidaCerrado);
        salidaAbierta = false;
        salidaPasando = false;
      }
    }
  }
}