/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Scan Events (Bridge: Scanner → Android Display)
 * ═══════════════════════════════════════════════════
 *
 * POST /api/scan-event  — Scanner Python envía el nombre del socio verificado
 * GET  /api/scan-event  — App Android hace polling para recibir el evento
 */

const express = require("express");
const { requireAdminKey } = require("../middleware/auth");
const { generateCardNumber } = require("../services/cryptoService");
const pool = require("../db/pool");

const router = express.Router();

// In-memory store for the latest scan event
let lastScanEvent = null;

/**
 * POST /api/scan-event
 * Called by run_scanner.py when a member is verified.
 * Protected by Admin API Key.
 *
 * Body: { member_name: "Juan Pérez" }
 */
router.post("/", requireAdminKey, (req, res) => {
  const { member_name, member_id, event_type } = req.body;
  if (!member_name || typeof member_name !== "string") {
    return res.status(400).json({ success: false, errors: ["member_name is required."] });
  }

  // event_type: "welcome" (check-in) | "farewell" (check-out) | default "welcome"
  const validTypes = ["welcome", "farewell"];
  const resolvedType = validTypes.includes(event_type) ? event_type : "welcome";

  lastScanEvent = {
    member_name: member_name.trim(),
    member_id: member_id || null,
    event_type: resolvedType,
    timestamp: Date.now(),
  };

  console.log(`📡 Scan event received: ${lastScanEvent.member_name} (${resolvedType})`);
  res.json({ success: true, event: lastScanEvent });
});

/**
 * POST /api/scan-event/card
 * Resolves a 16-digit card number to a member name and triggers a scan event.
 * Public for display convenience.
 */
router.post("/card", async (req, res) => {
  const { card_number } = req.body;
  if (!card_number) {
    return res.status(400).json({ success: false, errors: ["card_number is required."] });
  }

  const cleanCard = card_number.replace(/\s+/g, "").replace(/-/g, "");
  if (cleanCard.length !== 16 || !/^\d+$/.test(cleanCard)) {
    return res.status(400).json({ success: false, errors: ["El número de tarjeta debe tener 16 dígitos."] });
  }

  try {
    const result = await pool.query(
      "SELECT id, full_name, status FROM users WHERE status IN ('active', 'confirmed', 'completed')"
    );

    let matchedUser = null;
    for (const user of result.rows) {
      const generated = generateCardNumber(user.id).replace(/\s+/g, "");
      if (generated === cleanCard) {
        matchedUser = user;
        break;
      }
    }

    if (!matchedUser) {
      return res.status(404).json({ success: false, errors: ["Tarjeta no reconocida o socio inactivo."] });
    }

    lastScanEvent = {
      member_name: matchedUser.full_name,
      member_id: matchedUser.id,
      event_type: "welcome",
      timestamp: Date.now(),
    };

    const vehiclesResult = await pool.query(
      "SELECT id, nickname, vehicle AS vehicle_type, brand, model, year, color, plate, is_primary FROM user_vehicles WHERE user_id = $1 ORDER BY is_primary DESC, created_at ASC",
      [matchedUser.id]
    );

    console.log(`📡 Scan event triggered via card number lookup: ${lastScanEvent.member_name}`);
    res.json({ 
      success: true, 
      member_name: lastScanEvent.member_name, 
      member_id: lastScanEvent.member_id,
      vehicles: vehiclesResult.rows 
    });
  } catch (err) {
    console.error("Error resolving card number:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor.", err.message] });
  }
});

/**
 * GET /api/scan-event
 * Polled by the Android display app every few seconds.
 * Public (no auth required) — returns the latest event if < 30s old.
 */
router.get("/", (_req, res) => {
  if (!lastScanEvent) {
    return res.json({ success: true, event: null });
  }

  const ageMs = Date.now() - lastScanEvent.timestamp;
  const MAX_AGE_MS = 30_000; // 30 seconds

  if (ageMs > MAX_AGE_MS) {
    return res.json({ success: true, event: null });
  }

  res.json({ success: true, event: lastScanEvent });
});

/**
 * DELETE /api/scan-event
 * Called by the Android app after it has displayed the welcome message,
 * so duplicate polls don't re-trigger the welcome screen.
 */
router.delete("/", (_req, res) => {
  lastScanEvent = null;
  res.json({ success: true });
});

module.exports = router;
