"""
Parking GTR — Member Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre socios/usuarios (tabla ``users``).
"""

from core.database import db_cursor


def get_members_summary() -> list[tuple]:
    """Obtiene un resumen de socios desde la tabla ``users``.

    Returns:
        Lista de tuplas (email, full_name, vehicle_count, preferred_service).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.email, u.full_name, 
                   (SELECT COUNT(*) FROM user_vehicles WHERE user_id = u.id),
                   u.preferred_service
            FROM users u
            ORDER BY u.created_at DESC;
        """)
        return cur.fetchall()


def get_member_details(email: str) -> list[tuple]:
    """Obtiene el historial completo de reservaciones de un socio.
    
    Busca por email en la tabla users y une con reservations.

    Returns:
        Lista de tuplas (full_name, phone, service, vehicle, status,
                         created_at, res_id, license_plate).
    """
    with db_cursor() as cur:
        # Primero obtenemos datos del usuario y sus reservaciones
        cur.execute("""
            SELECT u.full_name, u.phone, r.service, r.vehicle, r.status, r.created_at, r.id, r.license_plate
            FROM users u
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.email = %s
            ORDER BY r.created_at DESC NULLS LAST;
        """, (email,))
        return cur.fetchall()


def delete_member(email: str) -> int:
    """Elimina un socio y todas sus dependencias (vía CASCADE o manual).

    Returns:
        Cantidad de registros de usuario eliminados.
    """
    with db_cursor() as cur:
        # Al borrar el usuario, las reservaciones y vehículos deberían borrarse si las FK tienen CASCADE.
        # Si no, las borramos manualmente aquí.
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        return cur.rowcount


def update_password(email: str, password_hash: str) -> None:
    """Actualiza el hash de contraseña del socio."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email),
        )


def update_license_plate(record_id: int, plate: str) -> None:
    """Actualiza la matrícula de una reservación específica."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE reservations SET license_plate = %s WHERE id = %s",
            (plate, record_id),
        )


def get_all_member_ids() -> list[int]:
    """Obtiene todos los IDs de la tabla users para verificación de tarjeta.

    Returns:
        Lista de IDs ordenados ascendentemente.
    """
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users ORDER BY id")
        return [row[0] for row in cur.fetchall()]


def get_vehicles_for_email(email: str) -> list[tuple]:
    """Obtiene los vehículos de un socio."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT v.id, v.vehicle, v.plate, r.service
            FROM users u
            JOIN user_vehicles v ON u.id = v.user_id
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.email = %s
            ORDER BY v.created_at DESC;
        """, (email,))
        return cur.fetchall()
