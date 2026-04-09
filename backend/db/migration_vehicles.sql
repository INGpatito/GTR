-- ═══════════════════════════════════════════════════
-- Parking GTR — Migration: User Vehicles + Stats
-- Run after schema.sql + migration_password_hash.sql
-- ═══════════════════════════════════════════════════

-- ── USER VEHICLES TABLE (max 3 per user) ───────────
CREATE TABLE IF NOT EXISTS user_vehicles (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER        NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
  nickname    VARCHAR(60)    NOT NULL DEFAULT 'My Vehicle',
  brand       VARCHAR(60),
  model       VARCHAR(60),
  year        SMALLINT,
  color       VARCHAR(30),
  plate       VARCHAR(20),
  vehicle     vehicle_type   DEFAULT 'sports',
  is_primary  BOOLEAN        DEFAULT FALSE,
  created_at  TIMESTAMPTZ    DEFAULT NOW()
);

CREATE INDEX idx_user_vehicles_user ON user_vehicles (user_id);

-- ── PREFERRED SERVICE COLUMN ───────────────────────
-- Adds a preferred_service column to reservations for the user's default choice
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'reservations' AND column_name = 'preferred_service'
  ) THEN
    ALTER TABLE reservations ADD COLUMN preferred_service service_type DEFAULT 'valet';
  END IF;
END $$;

-- ── FUNCTION: enforce max 3 vehicles per user ──────
CREATE OR REPLACE FUNCTION enforce_max_vehicles()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM user_vehicles WHERE user_id = NEW.user_id) >= 3 THEN
    RAISE EXCEPTION 'Maximum of 3 vehicles per user reached';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS check_max_vehicles ON user_vehicles;
CREATE TRIGGER check_max_vehicles
  BEFORE INSERT ON user_vehicles
  FOR EACH ROW
  EXECUTE FUNCTION enforce_max_vehicles();

-- ── FUNCTION: ensure only one primary per user ─────
CREATE OR REPLACE FUNCTION enforce_single_primary()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.is_primary = TRUE THEN
    UPDATE user_vehicles SET is_primary = FALSE
    WHERE user_id = NEW.user_id AND id != NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ensure_one_primary ON user_vehicles;
CREATE TRIGGER ensure_one_primary
  AFTER INSERT OR UPDATE ON user_vehicles
  FOR EACH ROW
  EXECUTE FUNCTION enforce_single_primary();
