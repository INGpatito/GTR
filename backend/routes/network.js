const express = require("express");
const router = express.Router();
const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");

const BLOCKED_MACS_FILE = path.join(__dirname, "../blocked_macs.json");
const WIFI_IFACE = "wlan0";

// Helper to load blocked MACs
function getBlockedMacs() {
    if (!fs.existsSync(BLOCKED_MACS_FILE)) {
        return [];
    }
    try {
        const data = fs.readFileSync(BLOCKED_MACS_FILE, "utf8");
        return JSON.parse(data || "[]");
    } catch (e) {
        return [];
    }
}

// Helper to save blocked MACs
function saveBlockedMacs(macs) {
    fs.writeFileSync(BLOCKED_MACS_FILE, JSON.stringify(macs, null, 2), "utf8");
}

// Run a shell command with sudo
function runSudo(command) {
    return new Promise((resolve) => {
        const fullCmd = `echo 'orangepi' | sudo -S ${command}`;
        exec(fullCmd, (err, stdout, stderr) => {
            resolve({
                success: !err,
                stdout: stdout.trim(),
                stderr: stderr.trim()
            });
        });
    });
}

// ── GET /api/network/status ────────────────────────
router.get("/status", async (req, res) => {
    try {
        // Check if auto-hotspot service is running
        const autoCheck = await runSudo("systemctl is-active auto-hotspot.service");
        const isAuto = autoCheck.stdout === "active";

        // Check active NetworkManager connections
        const nmCheck = await runSudo("nmcli -t -f NAME,DEVICE connection show --active");
        const activeConnections = nmCheck.stdout.split("\n").map(line => {
            const [name, device] = line.split(":");
            return { name, device };
        });

        const hotspotActive = activeConnections.some(c => c.name === "HotspotLocal" && c.device === WIFI_IFACE);
        
        let currentSSID = "Ninguno";
        const wifiActive = activeConnections.find(c => c.device === WIFI_IFACE && c.name !== "HotspotLocal");
        if (hotspotActive) {
            currentSSID = "GTR (Hotspot Activo)";
        } else if (wifiActive) {
            currentSSID = wifiActive.name;
        }

        // Get IP of hotspot if active
        let hotspotIP = "10.42.0.1";
        if (hotspotActive) {
            const ipCheck = await runSudo(`ip -4 addr show dev ${WIFI_IFACE}`);
            const match = ipCheck.stdout.match(/inet\s+(\d+\.\d+\.\d+\.\d+)/);
            if (match) {
                hotspotIP = match[1];
            }
        }

        res.json({
            success: true,
            auto_mode: isAuto,
            hotspot_active: hotspotActive,
            current_ssid: currentSSID,
            hotspot_ip: hotspotIP
        });
    } catch (err) {
        res.status(500).json({ success: false, errors: [err.message] });
    }
});

// ── POST /api/network/toggle-mode ───────────────────
router.post("/toggle-mode", async (req, res) => {
    const { mode } = req.body; // "auto", "manual-wifi", "manual-hotspot"
    if (!mode) {
        return res.status(400).json({ success: false, errors: ["El parámetro 'mode' es obligatorio."] });
    }

    try {
        if (mode === "auto") {
            // Enable and start auto-hotspot
            await runSudo("systemctl enable auto-hotspot.service");
            await runSudo("systemctl start auto-hotspot.service");
            res.json({ success: true, message: "Modo automático activado con éxito." });
        } else if (mode === "manual-wifi") {
            // Stop and disable auto-hotspot, force WiFi client mode
            await runSudo("systemctl disable auto-hotspot.service");
            await runSudo("systemctl stop auto-hotspot.service");
            await runSudo("nmcli connection down HotspotLocal");
            await runSudo("nmcli connection up MiWiFi || nmcli connection up INGpatito || nmcli connection up Pato || nmcli connection up Totalplay-ACA8-5G || true");
            res.json({ success: true, message: "Modo manual WiFi activado. Intentando conectar a la red WiFi guardada..." });
        } else if (mode === "manual-hotspot") {
            // Stop and disable auto-hotspot, force Hotspot GTR
            await runSudo("systemctl disable auto-hotspot.service");
            await runSudo("systemctl stop auto-hotspot.service");
            await runSudo("nmcli connection down MiWiFi || true");
            await runSudo("nmcli connection up HotspotLocal");
            res.json({ success: true, message: "Modo manual Hotspot (GTR) activado por la fuerza." });
        } else {
            res.status(400).json({ success: false, errors: ["Modo inválido. Use 'auto', 'manual-wifi' o 'manual-hotspot'."] });
        }
    } catch (err) {
        res.status(500).json({ success: false, errors: [err.message] });
    }
});

// ── GET /api/network/clients ────────────────────────
router.get("/clients", async (req, res) => {
    try {
        // Check active connections to verify if Hotspot is active
        const nmCheck = await runSudo("nmcli -t -f NAME,DEVICE connection show --active");
        const activeConnections = nmCheck.stdout.split("\n").map(line => {
            const [name, device] = line.split(":");
            return { name, device };
        });
        const hotspotActive = activeConnections.some(c => c.name === "HotspotLocal" && c.device === WIFI_IFACE);

        // If hotspot is down, there are by definition 0 clients connected to the GTR Hotspot
        if (!hotspotActive) {
            return res.json({ success: true, clients: [] });
        }

        // Get hotspot IP prefix to filter clients on the hotspot network
        let prefix = "10.42.0.";
        const ipCheck = await runSudo(`ip -4 addr show dev ${WIFI_IFACE}`);
        const match = ipCheck.stdout.match(/inet\s+(\d+\.\d+\.\d+\.\d+)/);
        if (match) {
            const parts = match[1].split(".");
            prefix = `${parts[0]}.${parts[1]}.${parts[2]}.`;
        }

        // Read blocked MACs
        const blockedMacs = getBlockedMacs();

        // Read ARP cache table
        const arpData = fs.readFileSync("/proc/net/arp", "utf8");
        const lines = arpData.split("\n");
        const clients = [];

        // Parse lines (skip header)
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            // Format: IP address HW type Flags HW address Mask Device
            const parts = line.split(/\s+/);
            if (parts.length >= 6) {
                const ip = parts[0];
                const flags = parts[2];
                const mac = parts[3].toLowerCase();
                const device = parts[5];

                // Filter only devices connected to the TP-Link WiFi adapter (hotspot)
                // and skip invalid MACs (like 00:00:00:00:00:00) and ensure they are on the hotspot subnet prefix
                if (device === WIFI_IFACE && mac !== "00:00:00:00:00:00" && flags !== "0x0" && ip.startsWith(prefix)) {
                    const isBlocked = blockedMacs.includes(mac);
                    clients.push({
                        ip,
                        mac,
                        blocked: isBlocked
                    });
                }
            }
        }

        res.json({ success: true, clients });
    } catch (err) {
        res.status(500).json({ success: false, errors: [err.message] });
    }
});

// ── POST /api/network/block ─────────────────────────
router.post("/block", async (req, res) => {
    const { mac, block } = req.body;
    if (!mac || block === undefined) {
        return res.status(400).json({ success: false, errors: ["Los parámetros 'mac' y 'block' son requeridos."] });
    }

    const cleanMac = mac.trim().toLowerCase();
    
    try {
        const blockedMacs = getBlockedMacs();

        if (block) {
            // Block
            if (!blockedMacs.includes(cleanMac)) {
                blockedMacs.push(cleanMac);
                saveBlockedMacs(blockedMacs);
            }

            // Apply iptables rules to drop all traffic from this MAC (safely checking existence first)
            await runSudo(`iptables -C INPUT -m mac --mac-source ${cleanMac} -j DROP || iptables -I INPUT -m mac --mac-source ${cleanMac} -j DROP`);
            await runSudo(`iptables -C FORWARD -m mac --mac-source ${cleanMac} -j DROP || iptables -I FORWARD -m mac --mac-source ${cleanMac} -j DROP`);
            
            res.json({ success: true, message: `Usuario con MAC ${cleanMac} bloqueado con éxito.` });
        } else {
            // Unblock
            const index = blockedMacs.indexOf(cleanMac);
            if (index > -1) {
                blockedMacs.splice(index, 1);
                saveBlockedMacs(blockedMacs);
            }

            // Remove iptables rules (safely checking existence first)
            await runSudo(`iptables -C INPUT -m mac --mac-source ${cleanMac} -j DROP && iptables -D INPUT -m mac --mac-source ${cleanMac} -j DROP || true`);
            await runSudo(`iptables -C FORWARD -m mac --mac-source ${cleanMac} -j DROP && iptables -D FORWARD -m mac --mac-source ${cleanMac} -j DROP || true`);

            res.json({ success: true, message: `Usuario con MAC ${cleanMac} desbloqueado con éxito.` });
        }
    } catch (err) {
        res.status(500).json({ success: false, errors: [err.message] });
    }
});

module.exports = router;
