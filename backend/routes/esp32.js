/**
 * GTR — ESP32 Bridge Routes
 * Proxy entre el panel web y la ESP32 fisica.
 * El servidor guarda la IP que la ESP32 registra al conectarse al AP GTR
 * y reenvía los comandos HTTP desde el panel hacia la placa.
 */

const express = require("express");
const router  = express.Router();
const http    = require("http");

// ── Estado global de la ESP32 (en memoria) ──────────
let esp32State = {
    ip:              null,
    registered_at:   null,
    last_heartbeat:  null,
    last_latency_ms: null,
    info:            null,
    command_log:     [],   // últimos 50 comandos
};

// Helper: petición HTTP GET a la ESP32 con timeout
function esp32Get(path, timeoutMs = 3000) {
    return new Promise((resolve, reject) => {
        if (!esp32State.ip) return reject(new Error("ESP32 no registrada"));
        const opts = {
            hostname: esp32State.ip,
            port:     80,
            path,
            method:   "GET",
            timeout:  timeoutMs,
        };
        const startTime = Date.now();
        const req = http.request(opts, (res) => {
            let body = "";
            res.on("data", d => body += d);
            res.on("end", () => resolve({
                status: res.statusCode,
                body,
                latency: Date.now() - startTime
            }));
        });
        req.on("timeout", () => { req.destroy(); reject(new Error("Timeout")); });
        req.on("error", reject);
        req.end();
    });
}

// ── POST /api/esp32/register ──────────────────────
// La ESP32 llama a este endpoint al arrancar y al reconectarse.
router.post("/register", (req, res) => {
    const { ip } = req.body;
    if (!ip) return res.status(400).json({ success: false, error: "IP requerida" });

    esp32State.ip            = ip.trim();
    esp32State.registered_at = Date.now();
    esp32State.last_heartbeat = Date.now();
    console.log(`[ESP32] Registrada en IP: ${esp32State.ip}`);
    res.json({ success: true, message: "Registrada" });
});

// ── GET /api/esp32/status ─────────────────────────
router.get("/status", (req, res) => {
    const connected = esp32State.ip &&
        esp32State.last_heartbeat &&
        (Date.now() - esp32State.last_heartbeat) < 30000; // <30s = viva

    res.json({
        success: true,
        esp32: {
            ...esp32State,
            connected: !!connected,
            command_log: esp32State.command_log.slice(-20),
        }
    });
});

// ── GET /api/esp32/heartbeat ──────────────────────
// Hace ping a la ESP32 y actualiza el estado.
router.get("/heartbeat", async (req, res) => {
    if (!esp32State.ip) {
        return res.json({ success: false, error: "ESP32 no registrada. Esperando conexión..." });
    }
    try {
        const r = await esp32Get("/api/heartbeat");
        esp32State.last_heartbeat  = Date.now();
        esp32State.last_latency_ms = r.latency;

        // Traer info completa
        try {
            const info = await esp32Get("/api/info");
            esp32State.info = JSON.parse(info.body);
        } catch(_) {}

        res.json({
            success:    true,
            alive:      true,
            latency_ms: r.latency,
            esp32_data: JSON.parse(r.body)
        });
    } catch(e) {
        esp32State.last_heartbeat = null;
        res.json({ success: false, error: e.message });
    }
});

// ── POST /api/esp32/command ───────────────────────
// Proxy de comandos: panel → OrangePi → ESP32.
router.post("/command", async (req, res) => {
    if (!esp32State.ip) {
        return res.status(503).json({ success: false, error: "ESP32 no registrada" });
    }

    const { command, params = {} } = req.body;
    let esp32Path = null;

    if      (command === "e_abrir")  esp32Path = "/api/entrada/abrir";
    else if (command === "e_cerrar") esp32Path = "/api/entrada/cerrar";
    else if (command === "s_abrir")  esp32Path = "/api/salida/abrir";
    else if (command === "s_cerrar") esp32Path = "/api/salida/cerrar";
    else if (command === "led_on")   esp32Path = "/api/led?state=1";
    else if (command === "led_off")  esp32Path = "/api/led?state=0";
    else if (command === "ping")     esp32Path = "/api/status";
    else return res.status(400).json({ success: false, error: "Comando desconocido" });

    const logEntry = { command, params, timestamp: Date.now(), status: "pending" };

    try {
        const r = await esp32Get(esp32Path, 5000);
        logEntry.status      = r.status === 200 ? "success" : "error";
        logEntry.response    = r.body;
        logEntry.latency_ms  = r.latency;

        esp32State.last_heartbeat  = Date.now();
        esp32State.last_latency_ms = r.latency;

        esp32State.command_log.push(logEntry);
        if (esp32State.command_log.length > 50) esp32State.command_log.shift();

        res.json({ success: true, latency_ms: r.latency, esp32_response: r.body });
    } catch(e) {
        logEntry.status   = "error";
        logEntry.response = e.message;
        esp32State.command_log.push(logEntry);
        if (esp32State.command_log.length > 50) esp32State.command_log.shift();
        res.status(500).json({ success: false, error: e.message });
    }
});

module.exports = router;
