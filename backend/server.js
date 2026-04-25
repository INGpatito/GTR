/**
 * ═══════════════════════════════════════════════════
 * Parking GTR — Backend API  (Hardened & Refactored)
 * ═══════════════════════════════════════════════════
 */

require("dotenv").config();
const express    = require("express");
const cors       = require("cors");
const helmet     = require("helmet");
const pool       = require("./db/pool");

// Import routes
const authRoutes = require("./routes/auth");
const reservationsRoutes = require("./routes/reservations");
const usersRoutes = require("./routes/users");
const vehiclesRoutes = require("./routes/vehicles");

const PORT = process.env.PORT || 3000;
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || "";
const BCRYPT_ROUNDS = 12;

const app = express();

// ── Security Middleware ────────────────────────────
app.use(helmet({
  contentSecurityPolicy: false, 
  crossOriginEmbedderPolicy: false,
}));

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
  allowedHeaders: ["Content-Type", "X-API-Key", "Authorization"],
}));

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

app.use("/api", authRoutes);
app.use("/api/reservations", reservationsRoutes);
app.use("/api/user", usersRoutes);
app.use("/api/user/:id/vehicles", vehiclesRoutes);

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
const server = app.listen(PORT, () => {
  console.log(`\n🚗 Parking GTR API running on http://localhost:${PORT}`);
  console.log(`   🔒 Helmet:      enabled`);
  console.log(`   🔒 Admin Key:   ${ADMIN_API_KEY ? "configured" : "⚠ NOT SET (dev mode)"}`);
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

  setTimeout(() => {
    console.error("   Forced shutdown after timeout.");
    process.exit(1);
  }, 10000);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT",  () => shutdown("SIGINT"));
