/**
 * Parking GTR — 332 Hardware Bridge Firmware (WiFi + Serial)
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
 * - GET http://<esp32_ip>/api/heartbeat                   -> Health-check rápido.
 * - GET http://<esp32_ip>/api/info                        -> Info detallada (uptime, memoria, señal).
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// --- Configuración de Red WiFi ---
// Modo 1: Red del hogar (Totalplay 2.4GHz) — para desarrollo
// IMPORTANTE: ESP32 solo soporta 2.4GHz, NO 5GHz
// #define WIFI_SSID "Totalplay-ACA8"  // Red 2.4GHz (la 5G no funciona con ESP32)
// #define WIFI_PASSWORD "ACA8E8A3hKKAEAxD"  // WPA-PSK

// Modo 2: Hotspot GTR (Orange Pi AP) — para producción
#define WIFI_SSID "GTR"  // Red abierta (sin contraseña)

// --- Servidor de Registro en la Orange Pi ---
// WiFi normal: 192.168.100.61:3000 (backend Node.js con PM2)
// Hotspot GTR: 10.42.0.1:3000
#define REGISTRATION_URL "http://10.42.0.1:3000/api/esp32/register"

// Pin del relevador / LED por defecto
#define DEFAULT_RELAY_PIN 2

// Intervalos (ms)
#define WIFI_RECONNECT_INTERVAL 15000   // Reintentar WiFi cada 15s si se pierde
#define REGISTRATION_RETRY_INTERVAL 10000 // Reintentar registro cada 10s si falla
#define HEARTBEAT_LOG_INTERVAL 60000    // Log de heartbeat cada 60s

WebServer server(80);

// Estado global
unsigned long bootTime = 0;
unsigned long lastWifiReconnectAttempt = 0;
unsigned long lastRegistrationAttempt = 0;
bool registrationDone = false;
int ledState = 0;

void executeOpenGate(int pin, int durationMs);
void setupWiFi();
void registerWithOrangePi();

// Manejadores del Servidor Web
void handleRoot();
void handleGate();
void handleLed();
void handleStatus();
void handleHeartbeat();
void handleInfo();

void setup() {
  Serial.begin(115200);
  bootTime = millis();
  
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
  server.on("/api/heartbeat", HTTP_GET, handleHeartbeat);
  server.on("/api/info", HTTP_GET, handleInfo);
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
  
  WiFi.mode(WIFI_STA); // Forzar modo Estación (cliente), evita crear su propia red
  WiFi.disconnect(true); // Borrar credenciales previas cacheadas
  delay(100);
  #ifdef WIFI_PASSWORD
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);  // Red con contraseña WPA
  #else
    WiFi.begin(WIFI_SSID);  // Red abierta (sin contraseña)
  #endif
  
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
  ledState = 0;
  
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
    registrationDone = true;
  } else {
    Serial.print("{\"status\":\"registration_failed\",\"error\":\"");
    Serial.print(http.errorToString(httpCode));
    Serial.println("\"}");
    registrationDone = false;
  }
  http.end();
  lastRegistrationAttempt = millis();
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
  ledState = state;
  
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

void handleHeartbeat() {
  // Health-check ultraligero — la Orange Pi lo usa para medir latencia
  String json = "{\"alive\":true,\"uptime_ms\":" + String(millis() - bootTime) + ",\"led_state\":" + String(ledState) + "}";
  server.send(200, "application/json", json);
}

void handleInfo() {
  // Info detallada del ESP32
  unsigned long uptimeMs = millis() - bootTime;
  unsigned long uptimeSec = uptimeMs / 1000;
  unsigned long hours = uptimeSec / 3600;
  unsigned long minutes = (uptimeSec % 3600) / 60;
  unsigned long seconds = uptimeSec % 60;
  
  String uptimeStr = String(hours) + "h " + String(minutes) + "m " + String(seconds) + "s";
  
  String json = "{";
  json += "\"device\":\"GTR-ESP32-Bridge\"";
  json += ",\"ip\":\"" + WiFi.localIP().toString() + "\"";
  json += ",\"mac\":\"" + WiFi.macAddress() + "\"";
  json += ",\"ssid\":\"" + String(WIFI_SSID) + "\"";
  json += ",\"rssi\":" + String(WiFi.RSSI());
  json += ",\"uptime_ms\":" + String(uptimeMs);
  json += ",\"uptime_str\":\"" + uptimeStr + "\"";
  json += ",\"free_heap\":" + String(ESP.getFreeHeap());
  json += ",\"led_state\":" + String(ledState);
  json += ",\"registered\":" + String(registrationDone ? "true" : "false");
  json += "}";
  
  server.send(200, "application/json", json);
}

void loop() {
  // --- Reconexión WiFi automática ---
  if (WiFi.status() != WL_CONNECTED) {
    unsigned long now = millis();
    if (now - lastWifiReconnectAttempt > WIFI_RECONNECT_INTERVAL) {
      lastWifiReconnectAttempt = now;
      Serial.println("{\"status\":\"wifi_reconnecting\",\"ssid\":\"" + String(WIFI_SSID) + "\"}");
      WiFi.disconnect();
      #ifdef WIFI_PASSWORD
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      #else
        WiFi.begin(WIFI_SSID);
      #endif
      
      // Esperar breve (3s max) sin bloquear demasiado el loop
      int retries = 0;
      while (WiFi.status() != WL_CONNECTED && retries < 6) {
        delay(500);
        retries++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("{\"status\":\"wifi_reconnected\",\"ip\":\"" + WiFi.localIP().toString() + "\"}");
        registrationDone = false; // Forzar re-registro con nueva IP posible
      }
    }
  }
  
  // --- Reintento de registro si falló previamente ---
  if (WiFi.status() == WL_CONNECTED && !registrationDone) {
    unsigned long now = millis();
    if (now - lastRegistrationAttempt > REGISTRATION_RETRY_INTERVAL) {
      registerWithOrangePi();
    }
  }

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
      ledState = state;
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
