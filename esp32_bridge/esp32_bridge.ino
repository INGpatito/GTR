/**
 * Parking GTR — ESP32 Hardware Bridge Firmware
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 * Escucha comandos a través de comunicación serial USB (115200 baudios).
 * Permite controlar relevadores u otros actuadores para abrir/cerrar barreras físicas.
 * 
 * Formatos de comando soportados:
 * 1. JSON: {"command": "open_gate", "pin": 2, "duration": 2000}
 * 2. Texto simple: OPEN:2:2000
 * 3. Ping: PING o {"command": "ping"}
 */

#include <Arduino.h>

// Pin del relevador / barrera por defecto
#define DEFAULT_RELAY_PIN 2

void executeOpenGate(int pin, int durationMs);

void setup() {
  Serial.begin(115200);
  pinMode(DEFAULT_RELAY_PIN, OUTPUT);
  digitalWrite(DEFAULT_RELAY_PIN, LOW); // Apagado/Cerrado por defecto
  
  // Mensaje de inicio en formato JSON para que el script Python lo detecte
  Serial.println("{\"status\":\"ready\",\"device\":\"GTR-ESP32-Bridge\"}");
}

void executeOpenGate(int pin, int durationMs) {
  // Asegurar dirección de pin
  pinMode(pin, OUTPUT);
  
  // Activar barrera (relevador)
  digitalWrite(pin, HIGH);
  Serial.print("{\"status\":\"executing\",\"action\":\"open_gate\",\"pin\":");
  Serial.print(pin);
  Serial.print(",\"duration\":");
  Serial.print(durationMs);
  Serial.println("}");
  
  // Esperar el tiempo de apertura
  delay(durationMs);
  
  // Desactivar barrera (cerrar relevador)
  digitalWrite(pin, LOW);
  Serial.print("{\"status\":\"success\",\"action\":\"close_gate\",\"pin\":");
  Serial.print(pin);
  Serial.println("}");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() == 0) return;
    
    // --- 1. Parser JSON Simple (Sin librerías externas) ---
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
    // --- 2. Parser de Texto Simple ---
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
