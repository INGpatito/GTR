"""
Parking GTR — Member Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre socios/usuarios (tabla ``users``),
sus vehículos (``user_vehicles``) y actividad (``reservations``).

Alineado con la BD actual y GTR-Profile.
"""

from core.database import db_cursor


# ══════════════════════════════════════════════════════
#  LISTADO DE SOCIOS
# ══════════════════════════════════════════════════════
def get_members_summary() -> list[tuple]:
    """Obtiene un resumen de socios desde la tabla ``users``.

    Returns:
        Lista de tuplas (id, full_name, email, membership_tier, vehicle_count, status).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.id, u.full_name, u.email, 
                   COALESCE(u.membership_tier, 'none'),
                   (SELECT COUNT(*) FROM user_vehicles WHERE user_id = u.id),
                   COALESCE(u.status, 'pending')
            FROM users u
            ORDER BY u.created_at DESC;
        """)
        return cur.fetchall()


# ══════════════════════════════════════════════════════
#  DETALLE DE UN SOCIO
# ══════════════════════════════════════════════════════
def get_member_by_id(user_id: int) -> tuple | None:
    """Obtiene los datos principales de un socio por su ID.

    Returns:
        Tupla (id, full_name, email, phone, preferred_service,
               membership_tier, status, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, full_name, email, phone, preferred_service,
                   COALESCE(membership_tier, 'none'), 
                   COALESCE(status, 'pending'), created_at
            FROM users
            WHERE id = %s
        """, (user_id,))
        return cur.fetchone()


def get_member_by_email(email: str) -> tuple | None:
    """Obtiene los datos principales de un socio por su email.

    Returns:
        Tupla (id, full_name, email, phone, preferred_service,
               membership_tier, status, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, full_name, email, phone, preferred_service,
                   COALESCE(membership_tier, 'none'), 
                   COALESCE(status, 'pending'), created_at
            FROM users
            WHERE email = %s
        """, (email,))
        return cur.fetchone()


# ══════════════════════════════════════════════════════
#  VEHÍCULOS DEL SOCIO (desde user_vehicles)
# ══════════════════════════════════════════════════════
def get_member_vehicles(user_id: int) -> list[tuple]:
    """Obtiene los vehículos registrados de un socio.

    Returns:
        Lista de tuplas (id, nickname, vehicle, brand, model, year,
                         color, plate, is_primary).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, nickname, vehicle, brand, model, year,
                   color, plate, is_primary
            FROM user_vehicles
            WHERE user_id = %s
            ORDER BY is_primary DESC, created_at ASC
        """, (user_id,))
        return cur.fetchall()


# ══════════════════════════════════════════════════════
#  ACTIVIDAD DEL SOCIO (desde reservations)
# ══════════════════════════════════════════════════════
def get_member_activity(user_id: int, limit: int = 10) -> list[tuple]:
    """Obtiene el historial de actividad reciente de un socio.

    Returns:
        Lista de tuplas (id, service, vehicle, status, created_at).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, service, vehicle, status, created_at
            FROM reservations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        return cur.fetchall()


# ══════════════════════════════════════════════════════
#  MEMBRESÍA
# ══════════════════════════════════════════════════════
VALID_TIERS = ("silver", "gold", "platinum", "none")

def update_membership_tier(user_id: int, tier: str) -> bool:
    """Actualiza el tier de membresía de un socio.

    Returns:
        True si se actualizó exitosamente, False si no.
    """
    if tier not in VALID_TIERS:
        raise ValueError(f"Tier inválido: {tier}. Debe ser: {', '.join(VALID_TIERS)}")
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET membership_tier = %s WHERE id = %s",
            (tier, user_id),
        )
        return cur.rowcount > 0


# ══════════════════════════════════════════════════════
#  ELIMINACIÓN
# ══════════════════════════════════════════════════════
def delete_member(email: str) -> int:
    """Elimina un socio y todas sus dependencias.

    Returns:
        Cantidad de registros de usuario eliminados.
    """
    with db_cursor() as cur:
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        return cur.rowcount


def delete_member_by_id(user_id: int) -> int:
    """Elimina un socio por su ID.

    Returns:
        Cantidad de registros eliminados.
    """
    with db_cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return cur.rowcount


# ══════════════════════════════════════════════════════
#  SEGURIDAD
# ══════════════════════════════════════════════════════
def update_password(email: str, password_hash: str) -> None:
    """Actualiza el hash de contraseña del socio."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email),
        )


def update_license_plate(vehicle_id: int, plate: str) -> None:
    """Actualiza la matrícula de un vehículo específico."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE user_vehicles SET plate = %s WHERE id = %s",
            (plate, vehicle_id),
        )


def get_vehicles_for_email(email: str) -> list[tuple]:
    """Obtiene los vehículos de un socio por su email.
    
    Returns:
        Lista de tuplas (vehicle_id, vehicle_type, plate, nickname, brand, model).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT v.id, v.vehicle, v.plate, v.nickname, v.brand, v.model
            FROM users u
            JOIN user_vehicles v ON u.id = v.user_id
            WHERE u.email = %s
            ORDER BY v.is_primary DESC, v.created_at ASC
        """, (email,))
        return cur.fetchall()


def get_all_member_ids() -> list[int]:
    """Obtiene todos los IDs de la tabla users.

    Returns:
        Lista de IDs ordenados ascendentemente.
    """
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users ORDER BY id")
        return [row[0] for row in cur.fetchall()]
