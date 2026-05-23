-- ═══════════════════════════════════════════════════
-- Parking GTR — Membership Tier Migration
-- ═══════════════════════════════════════════════════

-- Add membership_tier column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'none';
