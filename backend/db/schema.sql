-- ═══════════════════════════════════════════════════
-- Parking GTR — PostgreSQL Schema
-- ═══════════════════════════════════════════════════

-- Create database (run as superuser if needed)
-- CREATE DATABASE parking_gtr;

-- Connect to parking_gtr before running the rest:
-- \c parking_gtr

-- ── ENUM TYPES ─────────────────────────────────────
CREATE TYPE reservation_status AS ENUM (
  'pending',
  'confirmed',
  'cancelled',
  'completed'
);

CREATE TYPE vehicle_type AS ENUM (
  'sports',
  'suv',
  'sedan',
  'convertible',
  'exotic'
);

CREATE TYPE service_type AS ENUM (
  'valet',
  'monthly',
  'event',
  'concierge',
  'fleet'
);

-- ── RESERVATIONS TABLE ─────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
  id            SERIAL PRIMARY KEY,
  full_name     VARCHAR(120)       NOT NULL,
  email         VARCHAR(255)       NOT NULL,
  phone         VARCHAR(30),
  service       service_type,
  vehicle       vehicle_type       DEFAULT 'sports',
  arrival_date  DATE,
  arrival_time  TIME,
  message       TEXT,
  status        reservation_status DEFAULT 'pending',
  lang          CHAR(2)            DEFAULT 'en',
  ip_address    VARCHAR(45),
  created_at    TIMESTAMPTZ        DEFAULT NOW(),
  updated_at    TIMESTAMPTZ        DEFAULT NOW()
);

-- ── INDEXES ────────────────────────────────────────
CREATE INDEX idx_reservations_email      ON reservations (email);
CREATE INDEX idx_reservations_status     ON reservations (status);
CREATE INDEX idx_reservations_created_at ON reservations (created_at DESC);

-- ── UPDATED_AT TRIGGER ─────────────────────────────
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON reservations
  FOR EACH ROW
  EXECUTE FUNCTION update_modified_column();
