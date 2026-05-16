"""
Parking GTR — Member Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre socios/usuarios en la tabla ``users``.
"""

from core.database import db_cursor


def get_members_summary() -> list[tuple]:
    """Obtiene un resumen de socios desde la tabla users.

    Returns:
        Lista de tuplas (email, full_name, reservation_count, preferred_service).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.email, u.full_name, 
                   COUNT(r.id) AS reservation_count,
                   u.preferred_service
            FROM users u
            LEFT JOIN reservations r ON r.user_id = u.id
            GROUP BY u.id, u.email, u.full_name, u.preferred_service
            ORDER BY u.created_at DESC;
        """)
        return cur.fetchall()


def get_member_details(email: str) -> list[tuple]:
    """Obtiene el historial completo de reservaciones de un socio.

    Returns:
        Lista de tuplas (full_name, phone, service, vehicle, status,
                         created_at, id).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT u.full_name, u.phone, r.service, r.vehicle, r.status, "
            "r.created_at, r.id "
            "FROM reservations r "
            "JOIN users u ON r.user_id = u.id "
            "WHERE u.email = %s ORDER BY r.created_at DESC",
            (email,),
        )
        return cur.fetchall()


def delete_member(email: str) -> int:
    """Elimina un socio y todas sus reservaciones y vehículos.

    Returns:
        1 si el usuario fue eliminado, 0 si no se encontró.
    """
    with db_cursor() as cur:
        # Get user ID first
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if not row:
            return 0
        user_id = row[0]
        
        # Delete vehicles (CASCADE should handle this but be explicit)
        cur.execute("DELETE FROM user_vehicles WHERE user_id = %s", (user_id,))
        # Delete reservations
        cur.execute("DELETE FROM reservations WHERE user_id = %s", (user_id,))
        # Delete user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return 1


def update_password(email: str, password_hash: str) -> None:
    """Actualiza el hash de contraseña del usuario."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email),
        )


def get_all_member_ids() -> list[int]:
    """Obtiene todos los IDs de usuarios para verificación de tarjeta.

    Returns:
        Lista de IDs ordenados ascendentemente.
    """
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users ORDER BY id")
        return [row[0] for row in cur.fetchall()]


def get_vehicles_for_email(email: str) -> list[tuple]:
    """Obtiene los vehículos registrados de un socio.

    Returns:
        Lista de tuplas (id, vehicle, service).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT r.id, r.vehicle, r.service "
            "FROM reservations r "
            "JOIN users u ON r.user_id = u.id "
            "WHERE u.email = %s ORDER BY r.created_at DESC",
            (email,),
        )
        return cur.fetchall()
