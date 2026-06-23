/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Parking Spots & Requests Routes
 * ═══════════════════════════════════════════════════
 *
 * GET    /api/parking/spots              — All 24 spots with status
 * GET    /api/parking/spots/:floor       — Spots for a specific floor
 * POST   /api/parking/request            — Android sends check_in/check_out/heliport request
 * GET    /api/parking/request/pending     — Admin gets pending requests
 * GET    /api/parking/request/:userId/status — User polls request status
 * PATCH  /api/parking/request/:id/approve — Admin approves (check_in without spot, check_out frees spots)
 * PATCH  /api/parking/request/:id/reject  — Admin rejects
 * POST   /api/parking/spot/select         — User selects a spot after check_in approval
 * GET    /api/parking/heliport            — Heliport status
 * POST   /api/parking/checkout/:spotId    — Free a spot
 */

const express = require("express");
const pool = require("../db/pool");

const router = express.Router();

// ── GET /api/parking/spots ────────────────────────
router.get("/spots", async (_req, res) => {
  try {
    const result = await pool.query(`
      SELECT ps.id, ps.spot_number, ps.floor, ps.spot_label, ps.status,
             ps.occupied_by_user_id, ps.occupied_by_vehicle_id, ps.occupied_at,
             u.full_name AS user_name,
             uv.nickname AS vehicle_nickname, uv.brand, uv.model, uv.plate
      FROM parking_spots ps
      LEFT JOIN users u ON ps.occupied_by_user_id = u.id
      LEFT JOIN user_vehicles uv ON ps.occupied_by_vehicle_id = uv.id
      WHERE ps.floor > 0
      ORDER BY ps.floor, ps.spot_number
    `);
    res.json({ success: true, spots: result.rows });
  } catch (err) {
    console.error("Error fetching parking spots:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── GET /api/parking/spots/:floor ─────────────────
router.get("/spots/:floor", async (req, res) => {
  const floor = parseInt(req.params.floor, 10);
  if (isNaN(floor) || floor < 0 || floor > 3) {
    return res.status(400).json({ success: false, errors: ["Piso inválido (0-3)."] });
  }
  try {
    const result = await pool.query(
      `SELECT ps.id, ps.spot_number, ps.floor, ps.spot_label, ps.status,
              ps.occupied_by_user_id, ps.occupied_by_vehicle_id,
              u.full_name AS user_name,
              uv.nickname AS vehicle_nickname, uv.plate
       FROM parking_spots ps
       LEFT JOIN users u ON ps.occupied_by_user_id = u.id
       LEFT JOIN user_vehicles uv ON ps.occupied_by_vehicle_id = uv.id
       WHERE ps.floor = $1
       ORDER BY ps.spot_number`,
      [floor]
    );
    res.json({ success: true, spots: result.rows });
  } catch (err) {
    console.error("Error fetching floor spots:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── GET /api/parking/heliport ─────────────────────
router.get("/heliport", async (_req, res) => {
  try {
    const result = await pool.query(`
      SELECT ps.id, ps.spot_label, ps.status,
             ps.occupied_by_user_id, ps.occupied_at,
             u.full_name AS user_name
      FROM parking_spots ps
      LEFT JOIN users u ON ps.occupied_by_user_id = u.id
      WHERE ps.floor = 0 AND ps.spot_label = 'HELI-01'
      LIMIT 1
    `);
    if (result.rows.length === 0) {
      return res.json({ success: true, heliport: { status: "unavailable" } });
    }
    res.json({ success: true, heliport: result.rows[0] });
  } catch (err) {
    console.error("Error fetching heliport:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── POST /api/parking/request ─────────────────────
router.post("/request", async (req, res) => {
  const { user_id, vehicle_id, request_type } = req.body;

  if (!user_id || !request_type) {
    return res.status(400).json({ success: false, errors: ["user_id y request_type son requeridos."] });
  }
  if (!["check_in", "check_out", "heliport"].includes(request_type)) {
    return res.status(400).json({ success: false, errors: ["request_type debe ser 'check_in', 'check_out', o 'heliport'."] });
  }

  try {
    // Cancel any previous pending requests of the same type from this user
    await pool.query(
      `UPDATE parking_requests SET status = 'rejected' WHERE user_id = $1 AND status = 'pending'`,
      [user_id]
    );

    const result = await pool.query(
      `INSERT INTO parking_requests (user_id, vehicle_id, request_type)
       VALUES ($1, $2, $3) RETURNING *`,
      [user_id, vehicle_id || null, request_type]
    );

    console.log(`🅿️ Parking request created: user=${user_id}, type=${request_type}`);
    res.json({ success: true, request: result.rows[0] });
  } catch (err) {
    console.error("Error creating parking request:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── GET /api/parking/request/pending ──────────────
router.get("/request/pending", async (_req, res) => {
  try {
    const result = await pool.query(`
      SELECT pr.id, pr.user_id, pr.vehicle_id, pr.request_type, pr.status, pr.created_at,
             u.full_name, u.email,
             uv.nickname AS vehicle_nickname, uv.brand, uv.model, uv.plate, uv.vehicle AS vehicle_type
      FROM parking_requests pr
      JOIN users u ON pr.user_id = u.id
      LEFT JOIN user_vehicles uv ON pr.vehicle_id = uv.id
      WHERE pr.status = 'pending'
      ORDER BY pr.created_at ASC
    `);
    res.json({ success: true, requests: result.rows });
  } catch (err) {
    console.error("Error fetching pending requests:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── GET /api/parking/request/:userId/status ───────
router.get("/request/:userId/status", async (req, res) => {
  const userId = parseInt(req.params.userId, 10);
  try {
    const result = await pool.query(
      `SELECT id, request_type, status, spot_id, created_at, updated_at
       FROM parking_requests
       WHERE user_id = $1
       ORDER BY created_at DESC LIMIT 1`,
      [userId]
    );
    const request = result.rows[0] || null;
    res.json({ success: true, request });
  } catch (err) {
    console.error("Error fetching request status:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── PATCH /api/parking/request/:id/approve ────────
router.patch("/request/:id/approve", async (req, res) => {
  const requestId = parseInt(req.params.id, 10);
  const { spot_id } = req.body;

  try {
    // Get the request
    const reqResult = await pool.query(
      `SELECT * FROM parking_requests WHERE id = $1 AND status = 'pending'`,
      [requestId]
    );
    if (reqResult.rows.length === 0) {
      return res.status(404).json({ success: false, errors: ["Solicitud no encontrada o ya procesada."] });
    }

    const parkReq = reqResult.rows[0];

    if (parkReq.request_type === "check_in") {
      // For check_in: approve WITHOUT assigning spot.
      // The user will select a spot from the Android app after seeing the approval.
      await pool.query(
        `UPDATE parking_requests SET status = 'approved' WHERE id = $1`,
        [requestId]
      );

    } else if (parkReq.request_type === "check_out") {
      // For check_out: free the user's occupied spots immediately
      await pool.query(
        `UPDATE parking_spots SET status = 'available', occupied_by_user_id = NULL,
         occupied_by_vehicle_id = NULL, occupied_at = NULL
         WHERE occupied_by_user_id = $1 AND status = 'occupied'`,
        [parkReq.user_id]
      );
      await pool.query(
        `UPDATE parking_requests SET status = 'approved' WHERE id = $1`,
        [requestId]
      );

    } else if (parkReq.request_type === "heliport") {
      // For heliport: occupy the heliport spot
      const heliResult = await pool.query(
        `SELECT id FROM parking_spots WHERE floor = 0 AND spot_label = 'HELI-01' AND status = 'available'`
      );
      if (heliResult.rows.length === 0) {
        return res.status(400).json({ success: false, errors: ["Helipuerto no disponible."] });
      }
      const heliSpotId = heliResult.rows[0].id;
      await pool.query(
        `UPDATE parking_spots SET status = 'occupied', occupied_by_user_id = $1, occupied_at = NOW()
         WHERE id = $2`,
        [parkReq.user_id, heliSpotId]
      );
      await pool.query(
        `UPDATE parking_requests SET status = 'approved', spot_id = $1 WHERE id = $2`,
        [heliSpotId, requestId]
      );
    }

    console.log(`✅ Parking request ${requestId} approved (${parkReq.request_type})`);
    res.json({ success: true });
  } catch (err) {
    console.error("Error approving parking request:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── PATCH /api/parking/request/:id/reject ─────────
router.patch("/request/:id/reject", async (req, res) => {
  const requestId = parseInt(req.params.id, 10);
  try {
    const result = await pool.query(
      `UPDATE parking_requests SET status = 'rejected' WHERE id = $1 AND status = 'pending' RETURNING *`,
      [requestId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, errors: ["Solicitud no encontrada o ya procesada."] });
    }
    console.log(`❌ Parking request ${requestId} rejected`);
    res.json({ success: true });
  } catch (err) {
    console.error("Error rejecting parking request:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── POST /api/parking/spot/select ─────────────────
// Called by Android after check_in is approved — user selects a specific spot
router.post("/spot/select", async (req, res) => {
  const { user_id, vehicle_id, spot_id } = req.body;

  if (!user_id || !spot_id) {
    return res.status(400).json({ success: false, errors: ["user_id y spot_id son requeridos."] });
  }

  try {
    // Verify user has an approved check_in request
    const reqResult = await pool.query(
      `SELECT id FROM parking_requests
       WHERE user_id = $1 AND request_type = 'check_in' AND status = 'approved'
       ORDER BY created_at DESC LIMIT 1`,
      [user_id]
    );
    if (reqResult.rows.length === 0) {
      return res.status(400).json({ success: false, errors: ["No hay solicitud de ingreso aprobada para este usuario."] });
    }

    // Check if spot is available
    const spotResult = await pool.query(
      `SELECT * FROM parking_spots WHERE id = $1 AND status = 'available' AND floor > 0`,
      [spot_id]
    );
    if (spotResult.rows.length === 0) {
      return res.status(400).json({ success: false, errors: ["Espacio no disponible."] });
    }

    // Occupy the spot
    await pool.query(
      `UPDATE parking_spots SET status = 'occupied', occupied_by_user_id = $1,
       occupied_by_vehicle_id = $2, occupied_at = NOW()
       WHERE id = $3`,
      [user_id, vehicle_id || null, spot_id]
    );

    // Mark the request as completed with the selected spot
    const requestId = reqResult.rows[0].id;
    await pool.query(
      `UPDATE parking_requests SET status = 'completed', spot_id = $1 WHERE id = $2`,
      [spot_id, requestId]
    );

    const spotInfo = spotResult.rows[0];
    console.log(`🅿️ User ${user_id} selected spot ${spotInfo.spot_label} (floor ${spotInfo.floor})`);
    res.json({ success: true, spot: spotInfo });
  } catch (err) {
    console.error("Error selecting parking spot:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

// ── POST /api/parking/checkout/:spotId ────────────
router.post("/checkout/:spotId", async (req, res) => {
  const spotId = parseInt(req.params.spotId, 10);
  try {
    const result = await pool.query(
      `UPDATE parking_spots SET status = 'available', occupied_by_user_id = NULL,
       occupied_by_vehicle_id = NULL, occupied_at = NULL
       WHERE id = $1 RETURNING *`,
      [spotId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, errors: ["Espacio no encontrado."] });
    }
    console.log(`🚗 Spot ${spotId} freed`);
    res.json({ success: true, spot: result.rows[0] });
  } catch (err) {
    console.error("Error checking out spot:", err);
    res.status(500).json({ success: false, errors: ["Error interno del servidor."] });
  }
});

module.exports = router;
