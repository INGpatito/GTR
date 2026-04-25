const express = require("express");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const pool = require("../db/pool");
const { createLimiter } = require("../middleware/rateLimiter");
const { sanitizeString, validateReservation } = require("../middleware/sanitize");
const { requireAdminKey } = require("../middleware/auth");

const router = express.Router();
const BCRYPT_ROUNDS = 12;
const JWT_SECRET = process.env.JWT_SECRET || "fallback_dev_secret_change_me";
const JWT_EXPIRES = "7d";

// CREATE reservation (public, rate-limited)
router.post("/", createLimiter, async (req, res) => {
  const errors = validateReservation(req.body);
  if (errors.length) return res.status(400).json({ success: false, errors });

  const { name, email, phone, service, vehicle, date, time, message, lang, password } = req.body;
  const safeName = sanitizeString(name);
  const safeEmail = sanitizeString(email).toLowerCase();
  const safePhone = sanitizeString(phone || "") || null;
  const safeMessage = sanitizeString(message || "") || null;
  const ips = req.headers["x-forwarded-for"] || req.socket.remoteAddress || "";
  const ip = ips.split(",")[0].trim().substring(0, 45) || null;

  try {
    await pool.query('BEGIN');

    // 1. Find or create user
    let userResult = await pool.query("SELECT id, password_hash FROM users WHERE email = $1", [safeEmail]);
    let userId;

    if (userResult.rowCount > 0) {
      userId = userResult.rows[0].id;
      // Optionally update password if provided and user has no password
      if (password && password.length >= 6 && !userResult.rows[0].password_hash) {
         const hash = await bcrypt.hash(password, BCRYPT_ROUNDS);
         await pool.query("UPDATE users SET password_hash = $1 WHERE id = $2", [hash, userId]);
      }
    } else {
      let passwordHash = null;
      if (password && password.length >= 6) {
        passwordHash = await bcrypt.hash(password, BCRYPT_ROUNDS);
      }
      const newUser = await pool.query(
        `INSERT INTO users (full_name, email, phone, password_hash, preferred_service)
         VALUES ($1, $2, $3, $4, $5) RETURNING id`,
        [safeName, safeEmail, safePhone, passwordHash, service || 'valet']
      );
      userId = newUser.rows[0].id;
    }

    // 2. Create reservation
    const result = await pool.query(
      `INSERT INTO reservations (user_id, service, vehicle, arrival_date, arrival_time, message, lang, ip_address)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING id, service, vehicle, arrival_date, arrival_time, status, created_at`,
      [userId, service || null, vehicle || "sports", date || null, time || null, safeMessage, lang || "en", ip]
    );

    await pool.query('COMMIT');

    const reservation = result.rows[0];
    reservation.full_name = safeName;
    reservation.email = safeEmail;

    console.log(`✅ New reservation #${reservation.id} from ${safeEmail} (User ID: ${userId})`);

    const token = jwt.sign({ id: userId, email: safeEmail }, JWT_SECRET, { expiresIn: JWT_EXPIRES });
    
    // Fetch current user status to inform frontend
    const userStatusRes = await pool.query("SELECT status FROM users WHERE id = $1", [userId]);
    const userStatus = userStatusRes.rows[0]?.status || 'pending';

    res.status(201).json({ success: true, reservation, token, user_status: userStatus });

  } catch (err) {
    await pool.query('ROLLBACK');
    console.error("❌ Insert error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error. Please try again later."] });
  }
});

// LIST reservations (admin — protected)
router.get("/", requireAdminKey, async (req, res) => {
  const { status, limit = 50, offset = 0 } = req.query;
  let query = `
    SELECT r.*, u.full_name, u.email, u.phone 
    FROM reservations r
    JOIN users u ON r.user_id = u.id
  `;
  const params = [];

  if (status) {
    params.push(status);
    query += ` WHERE r.status = $${params.length}`;
  }

  query += " ORDER BY r.created_at DESC";
  params.push(Math.min(Number(limit) || 50, 200));
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
router.get("/:id", requireAdminKey, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid reservation ID."] });

  try {
    const result = await pool.query(`
      SELECT r.*, u.full_name, u.email, u.phone 
      FROM reservations r
      JOIN users u ON r.user_id = u.id
      WHERE r.id = $1
    `, [id]);
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Database query error."] });
  }
});

// UPDATE reservation status (admin — protected)
router.patch("/:id", requireAdminKey, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid reservation ID."] });

  const validStatuses = ["pending", "confirmed", "cancelled", "completed"];
  const { status } = req.body;
  if (!status || !validStatuses.includes(status)) {
    return res.status(400).json({ success: false, errors: [`Invalid status. Must be: ${validStatuses.join(", ")}`] });
  }

  try {
    const result = await pool.query("UPDATE reservations SET status = $1 WHERE id = $2 RETURNING *", [status, id]);
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["Reservation not found."] });
    res.json({ success: true, reservation: result.rows[0] });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Database update error."] });
  }
});

module.exports = router;
