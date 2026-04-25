const express = require("express");
const pool = require("../db/pool");
const { requireAuth } = require("../middleware/auth");
const { createLimiter } = require("../middleware/rateLimiter");
const { sanitizeString, VALID_VEHICLES } = require("../middleware/sanitize");

const router = express.Router({ mergeParams: true }); // Important: to access :id from parent router

// GET all vehicles for a user
router.get("/", requireAuth, async (req, res) => {
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

// ADD a vehicle
router.post("/", requireAuth, createLimiter, async (req, res) => {
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
router.put("/:vid", requireAuth, async (req, res) => {
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
router.delete("/:vid", requireAuth, async (req, res) => {
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

module.exports = router;
