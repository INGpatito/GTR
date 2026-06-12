-- ═══════════════════════════════════════════════════
-- Parking GTR — Migration: Parking Spots & Requests
-- Run after migration_users.sql
-- ═══════════════════════════════════════════════════

-- ── PARKING SPOTS TABLE (24 spots, 3 floors, 8 per floor) ──
CREATE TABLE IF NOT EXISTS parking_spots (
  id                  SERIAL PRIMARY KEY,
  spot_number         INTEGER      NOT NULL,
  floor               INTEGER      NOT NULL,
  spot_label          VARCHAR(10)  NOT NULL,
  status              VARCHAR(20)  DEFAULT 'available',
  occupied_by_user_id    INTEGER   REFERENCES users(id) ON DELETE SET NULL,
  occupied_by_vehicle_id INTEGER   REFERENCES user_vehicles(id) ON DELETE SET NULL,
  occupied_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ  DEFAULT NOW()
);

-- Constraint: spot_number + floor must be unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_parking_spots_number_floor
  ON parking_spots (spot_number, floor);

-- ── Insert 24 parking spots (8 per floor × 3 floors) ──
INSERT INTO parking_spots (spot_number, floor, spot_label) VALUES
  -- Piso 1 (spots 1-8)
  (1, 1, 'P1-01'), (2, 1, 'P1-02'), (3, 1, 'P1-03'), (4, 1, 'P1-04'),
  (5, 1, 'P1-05'), (6, 1, 'P1-06'), (7, 1, 'P1-07'), (8, 1, 'P1-08'),
  -- Piso 2 (spots 9-16)
  (1, 2, 'P2-01'), (2, 2, 'P2-02'), (3, 2, 'P2-03'), (4, 2, 'P2-04'),
  (5, 2, 'P2-05'), (6, 2, 'P2-06'), (7, 2, 'P2-07'), (8, 2, 'P2-08'),
  -- Piso 3 (spots 17-24)
  (1, 3, 'P3-01'), (2, 3, 'P3-02'), (3, 3, 'P3-03'), (4, 3, 'P3-04'),
  (5, 3, 'P3-05'), (6, 3, 'P3-06'), (7, 3, 'P3-07'), (8, 3, 'P3-08')
ON CONFLICT DO NOTHING;

-- ── Placeholder: Helicóptero (floor=0, para implementación futura) ──
INSERT INTO parking_spots (spot_number, floor, spot_label, status) VALUES
  (1, 0, 'HELI-01', 'maintenance')
ON CONFLICT DO NOTHING;

-- ── PARKING REQUESTS TABLE (Android → Admin communication) ──
CREATE TABLE IF NOT EXISTS parking_requests (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  vehicle_id      INTEGER      REFERENCES user_vehicles(id) ON DELETE SET NULL,
  request_type    VARCHAR(10)  NOT NULL CHECK (request_type IN ('check_in', 'check_out')),
  status          VARCHAR(20)  DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
  spot_id         INTEGER      REFERENCES parking_spots(id),
  created_at      TIMESTAMPTZ  DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parking_requests_status ON parking_requests (status);
CREATE INDEX IF NOT EXISTS idx_parking_requests_user   ON parking_requests (user_id);

-- ── Trigger: auto-update updated_at ──
CREATE OR REPLACE FUNCTION update_parking_request_modified()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_parking_request_updated_at ON parking_requests;
CREATE TRIGGER set_parking_request_updated_at
  BEFORE UPDATE ON parking_requests
  FOR EACH ROW
  EXECUTE FUNCTION update_parking_request_modified();
