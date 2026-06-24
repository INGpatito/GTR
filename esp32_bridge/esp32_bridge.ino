/**
 * Parking GTR — Dual Gate Hardware Bridge Firmware (WiFi + Serial)
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// --- Configuración de Red WiFi ---
#define WIFI_SSID "GTR"

// --- Servidor de Registro en la Orange Pi ---
#define REGISTRATION_URL "http://10.42.0.1:3000/api/esp32/register"

// Pin del LED de estado general
#define DEFAULT_RELAY_PIN 2

// Intervalos (ms)
#define WIFI_RECONNECT_INTERVAL 15000
#define REGISTRATION_RETRY_INTERVAL 10000

WebServer server(80);

// --- OBJETOS SERVO ---
Servo servoEntrada;
Servo servoSalida;

// --- CONFIGURACIÓN DE PINES ---
const int pinServoEntrada  = 18; 
const int pinServoSalida   = 19; 

// Sensores de Entrada
const int pinIREntradaAbrir   = 16;
const int pinTriggerEntrada   = 4; 
const int pinEchoEntrada      = 17;

// Sensores de Salida
const int pinTriggerSalida    = 5; 
const int pinEchoSalida       = 12;
const int pinIRSalidaCerrar   = 23;

// --- CONFIGURACIÓN DE ÁNGULOS ---
const int anguloEntradaCerrado = 180;
const int anguloEntradaAbierto = 90;

const int anguloSalidaCerrado  = 180;
const int anguloSalidaAbierto  = 90;

// --- VARIABLES DE ESTADO ---
bool entradaAbierta = false;
bool entradaPasando = false;

bool salidaAbierta = false;
bool salidaPasando = false;

unsigned long ultimoEscaneo = 0;
const int distanciaCorte = 10;

unsigned long bootTime = 0;
unsigned long lastWifiReconnectAttempt = 0;
unsigned long lastRegistrationAttempt = 0;
bool registrationDone = false;
int ledState = 0;

void setupWiFi();
void registerWithOrangePi();

void handleRoot();
void handleEntradaAbrir();
void handleEntradaCerrar();
void handleSalidaAbrir();
void handleSalidaCerrar();
void handleLed();
void handleStatus();
void handleHeartbeat();
void handleInfo();

// Función auxiliar para leer la distancia
long obtenerDistancia(int triggerPin, int echoPin) {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  
  long duracion = pulseIn(echoPin, HIGH, 30000);
  long distancia = duracion * 0.034 / 2;
  
  if (distancia == 0) return 999;
  return distancia;
}

void setup() {
  Serial.begin(115200);
  bootTime = millis();
  
  pinMode(DEFAULT_RELAY_PIN, OUTPUT);
  digitalWrite(DEFAULT_RELAY_PIN, LOW);

  // Inicializar Pines de Sensores
  pinMode(pinIREntradaAbrir, INPUT);
  pinMode(pinIRSalidaCerrar, INPUT);
  pinMode(pinTriggerEntrada, OUTPUT);
  pinMode(pinEchoEntrada, INPUT);
  pinMode(pinTriggerSalida, OUTPUT);
  pinMode(pinEchoSalida, INPUT);

  // Inicializar Servos
  servoEntrada.attach(pinServoEntrada);
  servoSalida.attach(pinServoSalida);
  servoEntrada.write(anguloEntradaCerrado);
  servoSalida.write(anguloSalidaCerrado);

  Serial.println("{\"status\":\"booting\",\"device\":\"GTR-ESP32-Bridge\"}");

  setupWiFi();

  // Rutas HTTP
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/entrada/abrir", HTTP_GET, handleEntradaAbrir);
  server.on("/api/entrada/cerrar", HTTP_GET, handleEntradaCerrar);
  server.on("/api/salida/abrir", HTTP_GET, handleSalidaAbrir);
  server.on("/api/salida/cerrar", HTTP_GET, handleSalidaCerrar);
  server.on("/api/led", HTTP_GET, handleLed);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/heartbeat", HTTP_GET, handleHeartbeat);
  server.on("/api/info", HTTP_GET, handleInfo);
  server.begin();
  
  Serial.println("{\"status\":\"ready\",\"device\":\"GTR-ESP32-Bridge\"}");
  
  if (WiFi.status() == WL_CONNECTED) {
    registerWithOrangePi();
  }
}

void setupWiFi() {
  Serial.print("{\"status\":\"wifi_connecting\",\"ssid\":\"");
  Serial.print(WIFI_SSID);
  Serial.println("\"}");
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);
  
  #ifdef WIFI_PASSWORD
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  #else
    WiFi.begin(WIFI_SSID);
  #endif
  
  int retries = 0;
  bool toggleLed = false;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    digitalWrite(DEFAULT_RELAY_PIN, toggleLed ? HIGH : LOW);
    toggleLed = !toggleLed;
    retries++;
  }
  
  digitalWrite(DEFAULT_RELAY_PIN, LOW);
  ledState = 0;
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("{\"status\":\"wifi_connected\",\"ip\":\"");
    Serial.print(WiFi.localIP().toString());
    Serial.print("\",\"ssid\":\"");
    Serial.print(WIFI_SSID);
    Serial.println("\"}");
    
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

// --- Rutas ---

void handleRoot() {
  server.send(200, "text/plain", "GTR ESP32 Dual Gate Bridge is Active!");
}

void handleEntradaAbrir() {
  servoEntrada.write(anguloEntradaAbierto);
  entradaAbierta = true;
  String json = "{\"status\":\"success\",\"action\":\"entrada_abrir\"}";
  server.send(200, "application/json", json);
  Serial.println(json);
}

void handleEntradaCerrar() {
  servoEntrada.write(anguloEntradaCerrado);
  entradaAbierta = false;
  entradaPasando = false;
  String json = "{\"status\":\"success\",\"action\":\"entrada_cerrar\"}";
  server.send(200, "application/json", json);
  Serial.println(json);
}

void handleSalidaAbrir() {
  servoSalida.write(anguloSalidaAbierto);
  salidaAbierta = true;
  String json = "{\"status\":\"success\",\"action\":\"salida_abrir\"}";
  server.send(200, "application/json", json);
  Serial.println(json);
}

void handleSalidaCerrar() {
  servoSalida.write(anguloSalidaCerrado);
  salidaAbierta = false;
  salidaPasando = false;
  String json = "{\"status\":\"success\",\"action\":\"salida_cerrar\"}";
  server.send(200, "application/json", json);
  Serial.println(json);
}

void handleLed() {
  int state = 0;
  if (server.hasArg("state")) state = server.arg("state").toInt();
  digitalWrite(DEFAULT_RELAY_PIN, state == 1 ? HIGH : LOW);
  ledState = state;
  String json = "{\"status\":\"success\",\"led_state\":" + String(state) + "}";
  server.send(200, "application/json", json);
  Serial.println(json);
}

void handleStatus() {
  String json = "{\"device\":\"GTR-ESP32-Bridge\",\"wifi_connected\":true,\"ip\":\"" + WiFi.localIP().toString() + "\",\"signal_strength\":" + String(WiFi.RSSI());
  json += ",\"entrada_abierta\":" + String(entradaAbierta ? "true" : "false");
  json += ",\"salida_abierta\":" + String(salidaAbierta ? "true" : "false");
  json += "}";
  server.send(200, "application/json", json);
}

void handleHeartbeat() {
  String json = "{\"alive\":true,\"uptime_ms\":" + String(millis() - bootTime) + ",\"led_state\":" + String(ledState) + "}";
  server.send(200, "application/json", json);
}

void handleInfo() {
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
  json += ",\"entrada_abierta\":" + String(entradaAbierta ? "true" : "false");
  json += ",\"salida_abierta\":" + String(salidaAbierta ? "true" : "false");
  json += "}";
  
  server.send(200, "application/json", json);
}

void loop() {
  // 1. Reconexión WiFi
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
      
      int retries = 0;
      while (WiFi.status() != WL_CONNECTED && retries < 6) {
        delay(500);
        retries++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("{\"status\":\"wifi_reconnected\",\"ip\":\"" + WiFi.localIP().toString() + "\"}");
        registrationDone = false;
      }
    }
  }
  
  // 2. Reintento de registro
  if (WiFi.status() == WL_CONNECTED && !registrationDone) {
    unsigned long now = millis();
    if (now - lastRegistrationAttempt > REGISTRATION_RETRY_INTERVAL) {
      registerWithOrangePi();
    }
  }

  // 3. Procesar peticiones HTTP
  if (WiFi.status() == WL_CONNECTED) {
    server.handleClient();
  }

  // 4. Lógica de Sensores Automáticos
  if (millis() - ultimoEscaneo > 80) {
    ultimoEscaneo = millis();

    // 🚗 CONTROL AUTOMÁTICO DE ENTRADA
    if (!entradaAbierta) {
      // Abre con el IR Externo
      if (digitalRead(pinIREntradaAbrir) == LOW) { 
        Serial.println("{\"status\":\"sensor\",\"msg\":\"IR Ext Entrada detectado. Abriendo...\"}");
        servoEntrada.write(anguloEntradaAbierto);
        entradaAbierta = true;
      }
    } else {
      // Cierra con el Ultrasónico Interno
      long distEntrada = obtenerDistancia(pinTriggerEntrada, pinEchoEntrada);
      if (distEntrada < distanciaCorte) {
        entradaPasando = true;
      } 
      else if (distEntrada >= distanciaCorte && entradaPasando) {
        Serial.println("{\"status\":\"sensor\",\"msg\":\"Ultrasonico Entrada despejado. Cerrando...\"}");
        delay(800);
        servoEntrada.write(anguloEntradaCerrado);
        entradaAbierta = false;
        entradaPasando = false;
      }
    }

    // 🚙 CONTROL AUTOMÁTICO DE SALIDA
    if (!salidaAbierta) {
      // Abre con el Ultrasónico Interno
      long distSalida = obtenerDistancia(pinTriggerSalida, pinEchoSalida);
      if (distSalida < distanciaCorte) {
        Serial.println("{\"status\":\"sensor\",\"msg\":\"Ultrasonico Salida detectado. Abriendo...\"}");
        servoSalida.write(anguloSalidaAbierto);
        salidaAbierta = true;
      }
    } else {
      // Cierra con el IR Externo
      if (digitalRead(pinIRSalidaCerrar) == LOW) {
        salidaPasando = true;
      } 
      else if (digitalRead(pinIRSalidaCerrar) == HIGH && salidaPasando) {
        Serial.println("{\"status\":\"sensor\",\"msg\":\"IR Ext Salida despejado. Cerrando...\"}");
        delay(800);
        servoSalida.write(anguloSalidaCerrado);
        salidaAbierta = false;
        salidaPasando = false;
      }
    }
  }

  // 5. Comandos Serial
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) return;
    
    if (input.startsWith("{\"") || input.startsWith("{")) {
      int cmdIndex = input.indexOf("\"command\"");
      if (cmdIndex != -1) {
        int startQuote = input.indexOf(':', cmdIndex);
        int valStart = input.indexOf('"', startQuote);
        int valEnd = input.indexOf('"', valStart + 1);
        String command = input.substring(valStart + 1, valEnd);
        
        if (command == "e_abrir") handleEntradaAbrir();
        else if (command == "e_cerrar") handleEntradaCerrar();
        else if (command == "s_abrir") handleSalidaAbrir();
        else if (command == "s_cerrar") handleSalidaCerrar();
        else if (command == "ping") Serial.println("{\"status\":\"pong\"}");
        else Serial.println("{\"status\":\"error\",\"message\":\"unknown_command\"}");
      }
    }
    else if (input.startsWith("E_ABRIR") || input.startsWith("e_abrir")) handleEntradaAbrir();
    else if (input.startsWith("E_CERRAR") || input.startsWith("e_cerrar")) handleEntradaCerrar();
    else if (input.startsWith("S_ABRIR") || input.startsWith("s_abrir")) handleSalidaAbrir();
    else if (input.startsWith("S_CERRAR") || input.startsWith("s_cerrar")) handleSalidaCerrar();
    else if (input.startsWith("LED:") || input.startsWith("led:")) {
      int state = input.substring(input.indexOf(':') + 1).toInt();
      digitalWrite(DEFAULT_RELAY_PIN, state == 1 ? HIGH : LOW);
      ledState = state;
      Serial.println("{\"status\":\"led_change\",\"state\":" + String(state) + "}");
    }
    else if (input == "PING" || input == "ping") Serial.println("{\"status\":\"pong\"}");
  }
}
