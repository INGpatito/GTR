-- ═══════════════════════════════════════════════════
-- Parking GTR — Users Migration
-- ═══════════════════════════════════════════════════

-- 1. Crear tabla users
CREATE TABLE IF NOT EXISTS users (
  id                SERIAL PRIMARY KEY,
  full_name         VARCHAR(120) NOT NULL,
  email             VARCHAR(255) UNIQUE NOT NULL,
  phone             VARCHAR(30),
  password_hash     TEXT,
  preferred_service service_type DEFAULT 'valet',
  status            VARCHAR(20) DEFAULT 'active',
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Migrar datos únicos de reservations a users
-- Usamos DISTINCT ON (email) para tomar la reservación más reciente de cada usuario
INSERT INTO users (full_name, email, phone, password_hash, preferred_service, created_at)
SELECT DISTINCT ON (LOWER(email))
       full_name,
       LOWER(email),
       phone,
       password_hash,
       COALESCE(service, 'valet'),
       created_at
FROM reservations
ORDER BY LOWER(email), created_at DESC
ON CONFLICT (email) DO NOTHING;

-- 3. Añadir user_id a reservations
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- 4. Actualizar user_id en reservations
UPDATE reservations r
SET user_id = u.id
FROM users u
WHERE LOWER(r.email) = u.email;

-- 5. Actualizar user_vehicles para apuntar a la nueva tabla users
ALTER TABLE user_vehicles DROP CONSTRAINT IF EXISTS user_vehicles_user_id_fkey;

UPDATE user_vehicles v
SET user_id = u.id
FROM reservations r, users u
WHERE v.user_id = r.id AND LOWER(r.email) = u.email;

ALTER TABLE user_vehicles ADD CONSTRAINT user_vehicles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 6. Hacer opcionales las columnas redundantes en reservations
ALTER TABLE reservations ALTER COLUMN full_name DROP NOT NULL;
ALTER TABLE reservations ALTER COLUMN email DROP NOT NULL;
