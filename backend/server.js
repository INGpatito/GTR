/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Backend API  (Hardened)
 * ═══════════════════════════════════════════════════
 *
 * Endpoints:
 *   POST  /api/reservations     — Create a new reservation (public, rate-limited)
 *   GET   /api/reservations     — List all reservations   (admin, API-key required)
 *   GET   /api/reservations/:id — Get one reservation     (admin, API-key required)
 *   PATCH /api/reservations/:id — Update status           (admin, API-key required)
 *   GET   /api/health           — Health check
 */

require("dotenv").config();
const express    = require("express");
const cors       = require("cors");
const helmet     = require("helmet");
const rateLimit  = require("express-rate-limit");
const bcrypt     = require("bcrypt");
const { Pool }   = require("pg");

// ── Config ─────────────────────────────────────────
const PORT       = process.env.PORT || 3000;
const BCRYPT_ROUNDS = 12;
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || "";

const pool = new Pool({
  host:     process.env.DB_HOST     || "localhost",
  port:     Number(process.env.DB_PORT) || 5432,
  user:     process.env.DB_USER     || "postgres",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME     || "parking_gtr",
});

const app = express();

// ── Security Middleware ────────────────────────────

// Helmet: sets 15+ HTTP security headers automatically
// (X-Frame-Options, Strict-Transport-Security, X-Content-Type-Options, etc.)
app.use(helmet({
  contentSecurityPolicy: false, // We handle CSP via meta tags on the frontend
  crossOriginEmbedderPolicy: false,
}));

// CORS
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
    : true,
  methods: ["GET", "POST", "PATCH"],
  allowedHeaders: ["Content-Type", "X-API-Key"],
}));

// Body parser with size limit (reject payloads > 16 KB)
app.use(express.json({ limit: "16kb" }));

// Rate limiter for public POST endpoint (15 requests per minute per IP)
const createLimiter = rateLimit({
  windowMs: 60 * 1000,           // 1 minute
  max: 15,                        // max 15 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    errors: ["Too many requests. Please wait a moment before trying again."],
  },
});

// ── Input Sanitization ─────────────────────────────
function sanitizeString(str) {
  if (typeof str !== "string") return str;
  return str
    .replace(/[<>]/g, "")           // strip angle brackets (basic XSS)
    .replace(/javascript:/gi, "")   // strip javascript: URIs
    .replace(/on\w+\s*=/gi, "")     // strip inline event handlers (onclick=, etc.)
    .trim();
}

// ── Admin Auth Middleware ──────────────────────────
function requireAdminKey(req, res, next) {
  if (!ADMIN_API_KEY) {
    // If no key configured, allow access (dev mode)
    return next();
  }

  const provided = req.headers["x-api-key"];
  if (!provided || provided !== ADMIN_API_KEY) {
    return res.status(401).json({
      success: false,
      errors: ["Unauthorized. A valid X-API-Key header is required."],
    });
  }
  next();
}

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

// Health check (public)
app.get("/api/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", db: "connected", timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ status: "error", db: "disconnected", error: err.message });
  }
});

// CREATE reservation (public, rate-limited)
app.post("/api/reservations", createLimiter, async (req, res) => {
  const errors = validateReservation(req.body);
  if (errors.length) {
    return res.status(400).json({ success: false, errors });
  }

  const {
    name, email, phone, service, vehicle,
    date, time, message, lang, password
  } = req.body;

  // Sanitize user-provided strings
  const safeName    = sanitizeString(name);
  const safeEmail   = sanitizeString(email).toLowerCase();
  const safePhone   = sanitizeString(phone || "") || null;
  const safeMessage = sanitizeString(message || "") || null;

  // Hash password if provided
  let passwordHash = null;
  if (password && password.length >= 6) {
    try {
      passwordHash = await bcrypt.hash(password, BCRYPT_ROUNDS);
    } catch (hashErr) {
      console.error("❌ Bcrypt hash error:", hashErr.message);
      return res.status(500).json({ success: false, errors: ["Server error hashing credentials."] });
    }
  }

  const ips = req.headers["x-forwarded-for"] || req.socket.remoteAddress || "";
  const ip = ips.split(",")[0].trim().substring(0, 45) || null;

  try {
    const result = await pool.query(
      `INSERT INTO reservations
        (full_name, email, phone, service, vehicle, arrival_date, arrival_time, message, lang, ip_address, password_hash)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
       RETURNING id, full_name, email, service, vehicle, arrival_date, arrival_time, status, created_at`,
      [
        safeName,
        safeEmail,
        safePhone,
        service || null,
        vehicle || "sports",
        date   || null,
        time   || null,
        safeMessage,
        lang   || "en",
        ip,
        passwordHash,
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

// LIST reservations (admin — protected)
app.get("/api/reservations", requireAdminKey, async (req, res) => {
  const { status, limit = 50, offset = 0 } = req.query;

  let query = "SELECT * FROM reservations";
  const params = [];

  if (status) {
    params.push(status);
    query += ` WHERE status = $${params.length}`;
  }

  query += " ORDER BY created_at DESC";
  params.push(Math.min(Number(limit) || 50, 200));  // cap at 200
  query += ` LIMIT $${params.length}`;
  params.push(Math.max(Number(offset) || 0, 0));
  query += ` OFFSET $${params.length}`;

  try {
    const result = await pool.query(query, params);
    res.json({ success: true, count: result.rowCount, reservations: result.rows });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Database query error."] });
  }
});

// GET single reservation (admin — protected)
app.get("/api/reservations/:id", requireAdminKey, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) {
    return res.status(400).json({ success: false, errors: ["Invalid reservation ID."] });
  }

  try {
    const result = await pool.query("SELECT * FROM reservations WHERE id = $1", [id]);
    if (result.rowCount === 0) {
      return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    }
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Database query error."] });
  }
});

// UPDATE reservation status (admin — protected)
app.patch("/api/reservations/:id", requireAdminKey, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) {
    return res.status(400).json({ success: false, errors: ["Invalid reservation ID."] });
  }

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
      [status, id]
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    }
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Database update error."] });
  }
});

// ── 404 catch-all ──────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ success: false, errors: ["Endpoint not found."] });
});

// ── Error handler ──────────────────────────────────
app.use((err, _req, res, _next) => {
  // Don't leak internal error details to the client
  console.error("Unhandled error:", err);
  res.status(500).json({ success: false, errors: ["Internal server error."] });
});

// ── Start ──────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚗 Parking GTR API running on http://localhost:${PORT}`);
  console.log(`   🔒 Helmet:      enabled`);
  console.log(`   🔒 Rate Limit:  15 req/min on POST`);
  console.log(`   🔒 Admin Key:   ${ADMIN_API_KEY ? "configured" : "⚠ NOT SET (dev mode)"}`);
  console.log(`   🔒 Bcrypt:      ${BCRYPT_ROUNDS} rounds\n`);
});
