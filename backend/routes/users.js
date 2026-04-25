const express = require("express");
const bcrypt = require("bcrypt");
const pool = require("../db/pool");
const { requireAuth } = require("../middleware/auth");
const { sanitizeString, VALID_SERVICES } = require("../middleware/sanitize");
const { generateCardNumber } = require("../services/cryptoService");

const router = express.Router();
const BCRYPT_ROUNDS = 12;

// GET USER INFO
router.get("/:id", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });
  try {
    const result = await pool.query(
      "SELECT id, full_name, email, phone, preferred_service, status, created_at FROM users WHERE id = $1", 
      [id]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    const user = result.rows[0];
    user.card_number = generateCardNumber(user.id);
    
    // Get latest reservation details for backward compatibility with frontend if needed
    const resResult = await pool.query(
      "SELECT service, vehicle, arrival_date, arrival_time, message, status as res_status FROM reservations WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
      [id]
    );
    if (resResult.rowCount > 0) {
       Object.assign(user, resResult.rows[0]);
    }

    res.json({ success: true, user });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// UPDATE USER INFO
router.put("/:id", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });
  
  const { name, phone } = req.body;
  try {
    const safeName = sanitizeString(name);
    const safePhone = sanitizeString(phone);
    
    const result = await pool.query(
      `UPDATE users 
       SET full_name=$1, phone=$2
       WHERE id=$3 
       RETURNING id, full_name, email, phone, preferred_service, status`,
      [safeName, safePhone, id]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    res.json({ success: true, user: result.rows[0] });
  } catch (err) {
    console.error("Update error: ", err);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// CHANGE PASSWORD
router.put("/:id/password", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  const { currentPassword, newPassword } = req.body;
  if (!currentPassword || !newPassword) {
    return res.status(400).json({ success: false, errors: ["Current and new password are required."] });
  }
  if (newPassword.length < 6) {
    return res.status(400).json({ success: false, errors: ["New password must be at least 6 characters."] });
  }

  try {
    const result = await pool.query("SELECT password_hash FROM users WHERE id = $1", [id]);
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });

    const user = result.rows[0];
    if (!user.password_hash) {
      return res.status(400).json({ success: false, errors: ["Account has no password set."] });
    }

    const match = await bcrypt.compare(currentPassword, user.password_hash);
    if (!match) {
      return res.status(401).json({ success: false, errors: ["Current password is incorrect."] });
    }

    const newHash = await bcrypt.hash(newPassword, BCRYPT_ROUNDS);
    await pool.query("UPDATE users SET password_hash = $1 WHERE id = $2", [newHash, id]);

    console.log(`🔑 Password changed for user #${id}`);
    res.json({ success: true, message: "Password updated successfully." });
  } catch (err) {
    console.error("Password change error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// USER STATS
router.get("/:id/stats", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  try {
    const [userRes, vehicleRes, resCountRes] = await Promise.all([
      pool.query("SELECT id, full_name, email, status, preferred_service, created_at FROM users WHERE id = $1", [id]),
      pool.query("SELECT COUNT(*) AS count FROM user_vehicles WHERE user_id = $1", [id]),
      pool.query("SELECT COUNT(*) AS count FROM reservations WHERE user_id = $1", [id])
    ]);

    if (userRes.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });

    const u = userRes.rows[0];
    const memberSince = new Date(u.created_at);
    const now = new Date();
    const memberDays = Math.floor((now - memberSince) / (1000 * 60 * 60 * 24));

    res.json({
      success: true,
      stats: {
        total_reservations: parseInt(resCountRes.rows[0].count, 10),
        vehicles_registered: parseInt(vehicleRes.rows[0].count, 10),
        max_vehicles: 3,
        member_since: u.created_at,
        member_days: memberDays,
        status: u.status,
        preferred_service: u.preferred_service || "valet",
      },
    });
  } catch (err) {
    console.error("Stats error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// UPDATE PREFERRED SERVICE
router.patch("/:id/service", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  const { service } = req.body;
  if (!service || !VALID_SERVICES.includes(service)) {
    return res.status(400).json({ success: false, errors: [`Invalid service. Must be: ${VALID_SERVICES.join(", ")}`] });
  }

  try {
    const result = await pool.query(
      "UPDATE users SET preferred_service=$1 WHERE id=$2 RETURNING id, preferred_service",
      [service, id]
    );
    if (result.rowCount === 0) return res.status(404).json({ success: false, errors: ["User not found."] });
    res.json({ success: true, preferred_service: result.rows[0].preferred_service });
  } catch (err) {
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

// USER ACTIVITY HISTORY
router.get("/:id/activity", requireAuth, async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (isNaN(id)) return res.status(400).json({ success: false, errors: ["Invalid ID."] });

  try {
    const result = await pool.query(
      `SELECT id, service, vehicle, arrival_date, arrival_time, status, created_at
       FROM reservations
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT 10`,
      [id]
    );

    res.json({ success: true, activity: result.rows });
  } catch (err) {
    console.error("Activity error:", err.message);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

module.exports = router;
