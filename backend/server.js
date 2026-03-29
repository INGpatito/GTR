/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Backend API
 * ═══════════════════════════════════════════════════
 *
 * Endpoints:
 *   POST /api/reservations   — Create a new reservation
 *   GET  /api/reservations   — List all reservations (admin)
 *   GET  /api/reservations/:id — Get one reservation
 *   PATCH /api/reservations/:id — Update status
 *   GET  /api/health          — Health check
 */

require("dotenv").config();
const express = require("express");
const cors    = require("cors");
const { Pool } = require("pg");

// ── Config ─────────────────────────────────────────
const PORT = process.env.PORT || 3000;

const pool = new Pool({
  host:     process.env.DB_HOST     || "localhost",
  port:     Number(process.env.DB_PORT) || 5432,
  user:     process.env.DB_USER     || "postgres",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME     || "parking_gtr",
});

const app = express();

// ── Middleware ──────────────────────────────────────
const allowedOrigins = (process.env.CORS_ORIGINS || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({
  origin: allowedOrigins.length
    ? (origin, cb) => {
        if (!origin || allowedOrigins.includes(origin)) cb(null, true);
        else cb(new Error("CORS: origin not allowed"));
      }
    : true, // allow all if none configured
  methods: ["GET", "POST", "PATCH"],
  allowedHeaders: ["Content-Type"],
}));

app.use(express.json());

// ── Validation helpers ─────────────────────────────
const VALID_SERVICES = ["valet", "monthly", "event", "concierge", "fleet"];
const VALID_VEHICLES = ["sports", "suv", "sedan", "convertible", "exotic"];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateReservation(body) {
  const errors = [];
  if (!body.name || body.name.trim().length < 2)
    errors.push("Full name is required (min 2 chars).");
  if (!body.email || !EMAIL_RE.test(body.email))
    errors.push("A valid email address is required.");
  if (body.service && !VALID_SERVICES.includes(body.service))
    errors.push(`Invalid service. Must be one of: ${VALID_SERVICES.join(", ")}`);
  if (body.vehicle && !VALID_VEHICLES.includes(body.vehicle))
    errors.push(`Invalid vehicle. Must be one of: ${VALID_VEHICLES.join(", ")}`);
  if (body.date) {
    const d = new Date(body.date);
    if (isNaN(d.getTime())) errors.push("Invalid arrival date.");
  }
  if (body.time && !/^\d{2}:\d{2}(:\d{2})?$/.test(body.time))
    errors.push("Invalid arrival time format (HH:MM).");
  return errors;
}

// ── Routes ─────────────────────────────────────────

// Health check
app.get("/api/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", db: "connected", timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ status: "error", db: "disconnected", error: err.message });
  }
});

// CREATE reservation
app.post("/api/reservations", async (req, res) => {
  const errors = validateReservation(req.body);
  if (errors.length) {
    return res.status(400).json({ success: false, errors });
  }

  const {
    name, email, phone, service, vehicle,
    date, time, message, lang
  } = req.body;

  const ip = req.headers["x-forwarded-for"] || req.socket.remoteAddress || null;

  try {
    const result = await pool.query(
      `INSERT INTO reservations
        (full_name, email, phone, service, vehicle, arrival_date, arrival_time, message, lang, ip_address)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
       RETURNING id, full_name, email, service, vehicle, arrival_date, arrival_time, status, created_at`,
      [
        name.trim(),
        email.trim().toLowerCase(),
        phone?.trim() || null,
        service || null,
        vehicle || "sports",
        date   || null,
        time   || null,
        message?.trim() || null,
        lang   || "en",
        ip,
      ]
    );

    const reservation = result.rows[0];
    console.log(`✅ New reservation #${reservation.id} from ${reservation.email}`);

    res.status(201).json({
      success: true,
      reservation,
    });

  } catch (err) {
    console.error("❌ Insert error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error. Please try again later."] });
  }
});

// LIST reservations (admin)
app.get("/api/reservations", async (req, res) => {
  const { status, limit = 50, offset = 0 } = req.query;

  let query = "SELECT * FROM reservations";
  const params = [];

  if (status) {
    params.push(status);
    query += ` WHERE status = $${params.length}`;
  }

  query += " ORDER BY created_at DESC";
  params.push(Number(limit));
  query += ` LIMIT $${params.length}`;
  params.push(Number(offset));
  query += ` OFFSET $${params.length}`;

  try {
    const result = await pool.query(query, params);
    res.json({ success: true, count: result.rowCount, reservations: result.rows });
  } catch (err) {
    res.status(500).json({ success: false, errors: [err.message] });
  }
});

// GET single reservation
app.get("/api/reservations/:id", async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM reservations WHERE id = $1", [req.params.id]);
    if (result.rowCount === 0) {
      return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    }
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: [err.message] });
  }
});

// UPDATE reservation status
app.patch("/api/reservations/:id", async (req, res) => {
  const validStatuses = ["pending", "confirmed", "cancelled", "completed"];
  const { status } = req.body;
  if (!status || !validStatuses.includes(status)) {
    return res.status(400).json({
      success: false,
      errors: [`Invalid status. Must be: ${validStatuses.join(", ")}`],
    });
  }

  try {
    const result = await pool.query(
      "UPDATE reservations SET status = $1 WHERE id = $2 RETURNING *",
      [status, req.params.id]
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    }
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: [err.message] });
  }
});

// ── 404 catch-all ──────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ success: false, errors: ["Endpoint not found."] });
});

// ── Error handler ──────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ success: false, errors: ["Internal server error."] });
});

// ── Start ──────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚗 Parking GTR API running on http://localhost:${PORT}`);
  console.log(`   POST /api/reservations  — Create reservation`);
  console.log(`   GET  /api/reservations  — List all`);
  console.log(`   GET  /api/health        — Health check\n`);
});
