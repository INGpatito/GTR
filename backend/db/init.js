/**
 * Parking GTR — Database initializer
 * Run: npm run db:init
 *
 * Reads schema.sql and executes it against the configured PostgreSQL.
 */

require("dotenv").config();
const fs   = require("fs");
const path = require("path");
const { Pool } = require("pg");

const pool = new Pool({
  host:     process.env.DB_HOST     || "localhost",
  port:     Number(process.env.DB_PORT) || 5432,
  user:     process.env.DB_USER     || "postgres",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME     || "parking_gtr",
});

async function init() {
  const schemaPath = path.join(__dirname, "schema.sql");
  const sql = fs.readFileSync(schemaPath, "utf-8");

  console.log("🔧 Connecting to PostgreSQL…");
  const client = await pool.connect();

  try {
    console.log("📄 Running schema.sql…");
    await client.query(sql);
    console.log("✅ Schema applied successfully.");
  } catch (err) {
    console.error("❌ Schema error:", err.message);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

init();
