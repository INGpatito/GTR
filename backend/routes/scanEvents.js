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
  const { member_name } = req.body;
  if (!member_name || typeof member_name !== "string") {
    return res.status(400).json({ success: false, errors: ["member_name is required."] });
  }

  lastScanEvent = {
    member_name: member_name.trim(),
    timestamp: Date.now(),
  };

  console.log(`📡 Scan event received: ${lastScanEvent.member_name}`);
  res.json({ success: true, event: lastScanEvent });
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
