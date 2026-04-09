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
  max:      5,                       // Max connections (optimized for Orange Pi RAM)
  idleTimeoutMillis: 30000,          // Close idle connections after 30s
  connectionTimeoutMillis: 5000,     // Fail fast if DB is unreachable
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
  methods: ["GET", "POST", "PATCH", "PUT", "DELETE"],
  allowedHeaders: ["Content-Type", "X-API-Key"],
}));

// Body parser with size limit (reject payloads > 16 KB)
app.use(express.json({ limit: "16kb" }));

// ── Request Logger ─────────────────────────────────
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    const ms = Date.now() - start;
    const ts = new Date().toISOString().slice(11, 19);
    console.log(`[${ts}] ${req.method} ${req.originalUrl} → ${res.statusCode} (${ms}ms)`);
  });
  next();
});

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

// LOGIN (public, rate-limited)
app.post("/api/login", createLimiter, async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ success: false, errors: ["Email and password required."] });
  try {
    const result = await pool.query(
      "SELECT id, full_name, password_hash, status FROM reservations WHERE email = $1 ORDER BY created_at DESC LIMIT 1",
      [email.toLowerCase()]
    );
    if (result.rowCount === 0) return res.status(401).json({ success: false, errors: ["Invalid credentials."] });
    
    const user = result.rows[0];
    if (!user.password_hash) return res.status(401).json({ success: false, errors: ["Account not configured for login."] });
    
    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ success: false, errors: ["Invalid credentials."] });
    
    res.json({ success: true, id: user.id, name: user.full_name, status: user.status });
  } catch (err) {
    console.error("Login error: ", err);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// GET USER INFO (for profile page)
app.get("/api/user/:id", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });
  try {
    const result = await pool.query(
      "SELECT id, full_name, email, phone, service, vehicle, arrival_date, arrival_time, message, status, created_at FROM reservations WHERE id = $1", 
      [id]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    res.json({ success: true, user: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// UPDATE USER INFO (for profile page)
app.put("/api/user/:id", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });
  
  const { name, phone, service, vehicle, date, time, message } = req.body;
  try {
    const safeName = sanitizeString(name);
    const safePhone = sanitizeString(phone);
    const safeMessage = sanitizeString(message);
    
    const result = await pool.query(
      `UPDATE reservations 
       SET full_name=$1, phone=$2, service=$3, vehicle=$4, arrival_date=$5, arrival_time=$6, message=$7
       WHERE id=$8 
       RETURNING id, full_name, email, phone, service, vehicle, arrival_date, arrival_time, message, status`,
      [
        safeName, safePhone, service, vehicle, 
        date || null, time || null, safeMessage, id
      ]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    res.json({ success: true, user: result.rows[0] });
  } catch (err) {
    console.error("Update error: ", err);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// ── USER VEHICLES CRUD ────────────────────────────

// GET all vehicles for a user
app.get("/api/user/:id/vehicles", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });
  try {
    const result = await pool.query(
      "SELECT * FROM user_vehicles WHERE user_id = $1 ORDER BY is_primary DESC, created_at ASC",
      [id]
    );
    res.json({ success: true, vehicles: result.rows, count: result.rowCount });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// ADD a vehicle (max 3 enforced by DB trigger)
app.post("/api/user/:id/vehicles", createLimiter, async (req, res) => {
  const userId = parseInt(req.params.id, 10);
  if (isNaN(userId)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  const { nickname, brand, model, year, color, plate, vehicle, is_primary } = req.body;

  if (!nickname || nickname.trim().length < 1) {
    return res.status(400).json({ success: false, errors: ["A vehicle nickname is required."] });
  }
  if (vehicle && !VALID_VEHICLES.includes(vehicle)) {
    return res.status(400).json({ success: false, errors: [`Invalid vehicle type. Must be: ${VALID_VEHICLES.join(", ")}`] });
  }

  try {
    const result = await pool.query(
      `INSERT INTO user_vehicles (user_id, nickname, brand, model, year, color, plate, vehicle, is_primary)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       RETURNING *`,
      [
        userId,
        sanitizeString(nickname),
        sanitizeString(brand || "") || null,
        sanitizeString(model || "") || null,
        year ? parseInt(year, 10) : null,
        sanitizeString(color || "") || null,
        sanitizeString(plate || "") || null,
        vehicle || "sports",
        is_primary || false,
      ]
    );
    res.status(201).json({ success: true, vehicle: result.rows[0] });
  } catch (err) {
    if (err.message.includes("Maximum of 3 vehicles")) {
      return res.status(400).json({ success: false, errors: ["You can register a maximum of 3 vehicles."] });
    }
    console.error("Vehicle insert error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// UPDATE a vehicle
app.put("/api/user/:id/vehicles/:vid", async (req, res) => {
  const userId = parseInt(req.params.id, 10);
  const vid = parseInt(req.params.vid, 10);
  if (isNaN(userId) || isNaN(vid)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  const { nickname, brand, model, year, color, plate, vehicle, is_primary } = req.body;

  try {
    const result = await pool.query(
      `UPDATE user_vehicles
       SET nickname=$1, brand=$2, model=$3, year=$4, color=$5, plate=$6, vehicle=$7, is_primary=$8
       WHERE id=$9 AND user_id=$10
       RETURNING *`,
      [
        sanitizeString(nickname || "My Vehicle"),
        sanitizeString(brand || "") || null,
        sanitizeString(model || "") || null,
        year ? parseInt(year, 10) : null,
        sanitizeString(color || "") || null,
        sanitizeString(plate || "") || null,
        vehicle || "sports",
        is_primary || false,
        vid, userId,
      ]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["Vehicle not found."] });
    res.json({ success: true, vehicle: result.rows[0] });
  } catch (err) {
    console.error("Vehicle update error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// DELETE a vehicle
app.delete("/api/user/:id/vehicles/:vid", async (req, res) => {
  const userId = parseInt(req.params.id, 10);
  const vid = parseInt(req.params.vid, 10);
  if (isNaN(userId) || isNaN(vid)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  try {
    const result = await pool.query(
      "DELETE FROM user_vehicles WHERE id=$1 AND user_id=$2 RETURNING id",
      [vid, userId]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["Vehicle not found."] });
    res.json({ success: true, deleted: vid });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// ── USER STATS ────────────────────────────────────

app.get("/api/user/:id/stats", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  try {
    const [userRes, vehicleRes] = await Promise.all([
      pool.query(
        `SELECT id, full_name, email, service, status, preferred_service, created_at,
                (SELECT COUNT(*) FROM reservations r2 WHERE r2.email = r.email) AS total_reservations
         FROM reservations r WHERE r.id = $1`, [id]
      ),
      pool.query("SELECT COUNT(*) AS count FROM user_vehicles WHERE user_id = $1", [id]),
    ]);

    if (userRes.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });

    const u = userRes.rows[0];
    const memberSince = new Date(u.created_at);
    const now = new Date();
    const memberDays = Math.floor((now - memberSince) / (1000 * 60 * 60 * 24));

    res.json({
      success: true,
      stats: {
        total_reservations: parseInt(u.total_reservations, 10),
        vehicles_registered: parseInt(vehicleRes.rows[0].count, 10),
        max_vehicles: 3,
        member_since: u.created_at,
        member_days: memberDays,
        status: u.status,
        preferred_service: u.preferred_service || u.service || "valet",
      },
    });
  } catch (err) {
    console.error("Stats error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// UPDATE preferred service
app.patch("/api/user/:id/service", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  const { service } = req.body;
  if (!service || !VALID_SERVICES.includes(service)) {
    return res.status(400).json({ success: false, errors: [`Invalid service. Must be: ${VALID_SERVICES.join(", ")}`] });
  }

  try {
    const result = await pool.query(
      "UPDATE reservations SET preferred_service=$1 WHERE id=$2 RETURNING id, preferred_service",
      [service, id]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    res.json({ success: true, preferred_service: result.rows[0].preferred_service });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// ── USER ACTIVITY HISTORY ─────────────────────────
app.get("/api/user/:id/activity", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  try {
    // Get the user's email first, then fetch all their reservations
    const userRes = await pool.query("SELECT email FROM reservations WHERE id = $1", [id]);
    if (userRes.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });

    const email = userRes.rows[0].email;
    const result = await pool.query(
      `SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status, created_at
       FROM reservations
       WHERE email = $1
       ORDER BY created_at DESC
       LIMIT 10`,
      [email]
    );

    res.json({ success: true, activity: result.rows });
  } catch (err) {
    console.error("Activity error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
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
const server = app.listen(PORT, () => {
  console.log(`\n🚗 Parking GTR API running on http://localhost:${PORT}`);
  console.log(`   🔒 Helmet:      enabled`);
  console.log(`   🔒 Rate Limit:  15 req/min on POST`);
  console.log(`   🔒 Admin Key:   ${ADMIN_API_KEY ? "configured" : "⚠ NOT SET (dev mode)"}`);
  console.log(`   🔒 Bcrypt:      ${BCRYPT_ROUNDS} rounds`);
  console.log(`   🔧 Pool:        max=${pool.options.max}, idle=${pool.options.idleTimeoutMillis}ms\n`);
});

// ── Graceful Shutdown ──────────────────────────────
function shutdown(signal) {
  console.log(`\n⚠ ${signal} received — shutting down gracefully...`);
  server.close(async () => {
    console.log("   HTTP server closed.");
    try {
      await pool.end();
      console.log("   DB pool drained. Goodbye.\n");
    } catch (err) {
      console.error("   Error closing DB pool:", err.message);
    }
    process.exit(0);
  });

  // Force exit after 10s if graceful shutdown fails
  setTimeout(() => {
    console.error("   Forced shutdown after timeout.");
    process.exit(1);
  }, 10000);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT",  () => shutdown("SIGINT"));
