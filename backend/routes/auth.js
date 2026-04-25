const express = require("express");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const pool = require("../db/pool");
const { createLimiter } = require("../middleware/rateLimiter");

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || "fallback_dev_secret_change_me";
const JWT_EXPIRES = "7d";

router.post("/login", createLimiter, async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ success: false, errors: ["Email and password required."] });
  try {
    const result = await pool.query(
      "SELECT id, full_name, email, password_hash, status FROM users WHERE email = $1 LIMIT 1",
      [email.toLowerCase()]
    );
    if (result.rowCount === 0) return res.status(401).json({ success: false, errors: ["Invalid credentials."] });
    
    const user = result.rows[0];
    // Allow login regardless of status — the profile page shows account status.
    // Previously this blocked 'pending' users from accessing their dashboard.
    if (!user.password_hash) return res.status(401).json({ success: false, errors: ["Account not configured for login."] });
    
    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ success: false, errors: ["Invalid credentials."] });
    
    const token = jwt.sign(
      { id: user.id, email: user.email },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES }
    );
    
    res.json({ success: true, id: user.id, name: user.full_name, status: user.status, token });
  } catch (err) {
    console.error("Login error: ", err);
    res.status(500).json({ success: false, errors: ["Server error."] });
  }
});

module.exports = router;
