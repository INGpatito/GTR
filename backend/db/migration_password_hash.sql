-- ═══════════════════════════════════════════════════
-- Parking GTR — Migration: Add password_hash column
-- ═══════════════════════════════════════════════════
-- Run this on the Orange Pi PostgreSQL database:
--   psql -U postgres -d parking_gtr -f migration_password_hash.sql

ALTER TABLE reservations
  ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) DEFAULT NULL;

-- Optional: add a comment for documentation
COMMENT ON COLUMN reservations.password_hash IS 'Bcrypt-hashed password for member portal login';
