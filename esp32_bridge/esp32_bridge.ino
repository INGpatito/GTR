/**
 * Parking GTR — ESP32 Hardware Bridge Firmware (WiFi + Serial)
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * 
 * Modos de conexión soportados de forma simultánea:
 * 1. USB-Serial: 115200 baudios (JSON o comandos cortos de texto).
 * 2. WiFi: Se conecta a la red GTR (u otra configurable) y levanta un WebServer.
 * 
 * Endpoints HTTP expuestos (Puerto 80):
 * - GET http://<esp32_ip>/api/gate?pin=2&duration=2000    -> Abre la pluma/gate.
 * - GET http://<esp32_ip>/api/led?state=1                 -> Enciende el LED de prueba (GPIO 2).
 * - GET http://<esp32_ip>/api/led?state=0                 -> Apaga el LED de prueba (GPIO 2).
 * - GET http://<esp32_ip>/api/status                      -> Consulta el estado del ESP32.
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// --- Configuración de Red WiFi ---
#define WIFI_SSID "GTR"
#define WIFI_PASSWORD "orangepi123" // Cambia esto por la contraseña de tu red/hotspot GTR

// --- Servidor de Registro en la Orange Pi ---
// 10.42.0.1 es la IP por defecto de la Orange Pi en su modo HotspotLocal.
#define REGISTRATION_URL "http://10.42.0.1:3001/api/esp32/register"

// Pin del relevador / LED por defecto
#define DEFAULT_RELAY_PIN 2

WebServer server(80);

void executeOpenGate(int pin, int durationMs);
void setupWiFi();
void registerWithOrangePi();

// Manejadores del Servidor Web
void handleRoot();
void handleGate();
void handleLed();
void handleStatus();

void setup() {
  Serial.begin(115200);
  
  // Configurar Pin del Relevador/LED
  pinMode(DEFAULT_RELAY_PIN, OUTPUT);
  digitalWrite(DEFAULT_RELAY_PIN, LOW); // Apagado por defecto

  Serial.println("{\"status\":\"booting\",\"device\":\"GTR-ESP32-Bridge\"}");

  // Intentar conectar a WiFi
  setupWiFi();

  // Configurar Rutas del Servidor HTTP
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/gate", HTTP_GET, handleGate);
  server.on("/api/led", HTTP_GET, handleLed);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.begin();
  
  Serial.println("{\"status\":\"ready\",\"device\":\"GTR-ESP32-Bridge\"}");
  
  // Registrar IP actual en el servidor de la Orange Pi
  if (WiFi.status() == WL_CONNECTED) {
    registerWithOrangePi();
  }
}

void setupWiFi() {
  Serial.print("{\"status\":\"wifi_connecting\",\"ssid\":\"");
  Serial.print(WIFI_SSID);
  Serial.println("\"}");
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  // Esperar conexión con timeout de 10 segundos
  int retries = 0;
  bool toggleLed = false;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    // Parpadear el LED durante la conexión
    digitalWrite(DEFAULT_RELAY_PIN, toggleLed ? HIGH : LOW);
    toggleLed = !toggleLed;
    retries++;
  }
  
  // Asegurar que el LED regrese a apagado al terminar
  digitalWrite(DEFAULT_RELAY_PIN, LOW);
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("{\"status\":\"wifi_connected\",\"ip\":\"");
    Serial.print(WiFi.localIP().toString());
    Serial.print("\",\"ssid\":\"");
    Serial.print(WIFI_SSID);
    Serial.println("\"}");
    
    // Doble parpadeo rápido para indicar éxito de WiFi
    for (int i = 0; i < 2; i++) {
      digitalWrite(DEFAULT_RELAY_PIN, HIGH);
      delay(100);
      digitalWrite(DEFAULT_RELAY_PIN, LOW);
      delay(100);
    }
  } else {
    Serial.println("{\"status\":\"wifi_failed\",\"message\":\"timeout_or_incorrect_credentials\"}");
  }
}

void registerWithOrangePi() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  http.begin(REGISTRATION_URL);
  http.addHeader("Content-Type", "application/json");
  
  String payload = "{\"ip\":\"" + WiFi.localIP().toString() + "\"}";
  
  Serial.print("{\"status\":\"registering_ip\",\"url\":\"");
  Serial.print(REGISTRATION_URL);
  Serial.println("\"}");
  
  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("{\"status\":\"registered\",\"http_code\":");
    Serial.print(httpCode);
    Serial.print(",\"response\":");
    Serial.print(response);
    Serial.println("}");
  } else {
    Serial.print("{\"status\":\"registration_failed\",\"error\":\"");
    Serial.print(http.errorToString(httpCode));
    Serial.println("\"}");
  }
  http.end();
}

void executeOpenGate(int pin, int durationMs) {
  pinMode(pin, OUTPUT);
  
  // Activar barrera (relevador)
  digitalWrite(pin, HIGH);
  Serial.print("{\"status\":\"executing\",\"action\":\"open_gate\",\"pin\":");
  Serial.print(pin);
  Serial.print(",\"duration\":");
  Serial.print(durationMs);
  Serial.println("}");
  
  // Mantener activo
  delay(durationMs);
  
  // Desactivar barrera
  digitalWrite(pin, LOW);
  Serial.print("{\"status\":\"success\",\"action\":\"close_gate\",\"pin\":");
  Serial.print(pin);
  Serial.println("}");
}

// --- Rutas del Servidor HTTP ---

void handleRoot() {
  server.send(200, "text/plain", "GTR ESP32 Hardware Bridge is Active!");
}

void handleGate() {
  int pin = DEFAULT_RELAY_PIN;
  int duration = 2000;
  
  if (server.hasArg("pin")) {
    pin = server.arg("pin").toInt();
  }
  if (server.hasArg("duration")) {
    duration = server.arg("duration").toInt();
  }
  
  // Responder al cliente HTTP primero para no bloquear la conexión
  String json = "{\"status\":\"success\",\"action\":\"open_gate\",\"pin\":" + String(pin) + ",\"duration\":" + String(duration) + "}";
  server.send(200, "application/json", json);
  
  // Ejecutar apertura física
  executeOpenGate(pin, duration);
}

void handleLed() {
  int state = 0;
  if (server.hasArg("state")) {
    state = server.arg("state").toInt();
  }
  
  pinMode(DEFAULT_RELAY_PIN, OUTPUT);
  digitalWrite(DEFAULT_RELAY_PIN, state == 1 ? HIGH : LOW);
  
  String json = "{\"status\":\"success\",\"led_state\":" + String(state) + "}";
  server.send(200, "application/json", json);
  
  Serial.print("{\"status\":\"led_change\",\"state\":");
  Serial.print(state);
  Serial.println("}");
}

void handleStatus() {
  String json = "{\"device\":\"GTR-ESP32-Bridge\",\"wifi_connected\":true,\"ip\":\"" + WiFi.localIP().toString() + "\",\"signal_strength\":" + String(WiFi.RSSI()) + "}";
  server.send(200, "application/json", json);
}

void loop() {
  // Procesar peticiones HTTP vía WiFi
  if (WiFi.status() == WL_CONNECTED) {
    server.handleClient();
  }

  // Procesar comandos vía USB Serial
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() == 0) return;
    
    // Parser JSON Simple
    if (input.startsWith("{\"") || input.startsWith("{")) {
      int cmdIndex = input.indexOf("\"command\"");
      int pinIndex = input.indexOf("\"pin\"");
      int durIndex = input.indexOf("\"duration\"");
      
      if (cmdIndex != -1) {
        int startQuote = input.indexOf(':', cmdIndex);
        int valStart = input.indexOf('"', startQuote);
        int valEnd = input.indexOf('"', valStart + 1);
        String command = input.substring(valStart + 1, valEnd);
        
        int pin = DEFAULT_RELAY_PIN;
        if (pinIndex != -1) {
          int startPinVal = input.indexOf(':', pinIndex) + 1;
          while (isspace(input[startPinVal]) || input[startPinVal] == ' ') startPinVal++;
          int endPinVal = startPinVal;
          while (isdigit(input[endPinVal])) endPinVal++;
          pin = input.substring(startPinVal, endPinVal).toInt();
        }
        
        int duration = 2000;
        if (durIndex != -1) {
          int startDurVal = input.indexOf(':', durIndex) + 1;
          while (isspace(input[startDurVal]) || input[startDurVal] == ' ') startDurVal++;
          int endDurVal = startDurVal;
          while (isdigit(input[endDurVal])) endDurVal++;
          duration = input.substring(startDurVal, endDurVal).toInt();
        }
        
        if (command == "open_gate") {
          executeOpenGate(pin, duration);
        } else if (command == "ping") {
          Serial.println("{\"status\":\"pong\"}");
        } else {
          Serial.print("{\"status\":\"error\",\"message\":\"unknown_command\",\"command\":\"");
          Serial.print(command);
          Serial.println("\"}");
        }
      } else {
        Serial.println("{\"status\":\"error\",\"message\":\"invalid_json\"}");
      }
    } 
    // Parser de Texto Simple
    else if (input.startsWith("OPEN:") || input.startsWith("open:")) {
      int colon1 = input.indexOf(':');
      int colon2 = input.indexOf(':', colon1 + 1);
      int pin = DEFAULT_RELAY_PIN;
      int duration = 2000;
      
      if (colon2 != -1) {
        pin = input.substring(colon1 + 1, colon2).toInt();
        duration = input.substring(colon2 + 1).toInt();
      } else {
        duration = input.substring(colon1 + 1).toInt();
      }
      executeOpenGate(pin, duration);
    } 
    else if (input.startsWith("LED:") || input.startsWith("led:")) {
      // Comando LED simple vía Serial (LED:1 para encender, LED:0 para apagar)
      int colon1 = input.indexOf(':');
      int state = input.substring(colon1 + 1).toInt();
      pinMode(DEFAULT_RELAY_PIN, OUTPUT);
      digitalWrite(DEFAULT_RELAY_PIN, state == 1 ? HIGH : LOW);
      Serial.print("{\"status\":\"led_change\",\"state\":");
      Serial.print(state);
      Serial.println("}");
    }
    else if (input == "PING" || input == "ping") {
      Serial.println("{\"status\":\"pong\"}");
    } 
    else {
      Serial.print("{\"status\":\"error\",\"message\":\"invalid_format\",\"input\":\"");
      Serial.print(input);
      Serial.println("\"}");
    }
  }
}
