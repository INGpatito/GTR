"""
Parking GTR — Member Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre socios/usuarios agrupados por email.
"""

from core.database import db_cursor


def get_members_summary() -> list[tuple]:
    """Obtiene un resumen de socios agrupados por email.

    Returns:
        Lista de tuplas (email, last_name, vehicle_count, max_service).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT email, MAX(full_name), COUNT(id), MAX(service)
            FROM reservations
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
            ORDER BY MAX(created_at) DESC;
        """)
        return cur.fetchall()


def get_member_details(email: str) -> list[tuple]:
    """Obtiene el historial completo de reservaciones de un socio.

    Returns:
        Lista de tuplas (full_name, phone, service, vehicle, status,
                         created_at, id, license_plate).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT full_name, phone, service, vehicle, status, created_at, id, license_plate "
            "FROM reservations WHERE email = %s ORDER BY created_at DESC",
            (email,),
        )
        return cur.fetchall()


def delete_member(email: str) -> int:
    """Elimina todas las reservaciones de un socio.

    Returns:
        Cantidad de registros eliminados.
    """
    with db_cursor() as cur:
        cur.execute("DELETE FROM reservations WHERE email = %s", (email,))
        return cur.rowcount


def update_password(email: str, password_hash: str) -> None:
    """Actualiza el hash de contraseña en todas las reservaciones del socio."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE reservations SET password_hash = %s WHERE email = %s",
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
    """Obtiene todos los IDs de reservaciones para verificación de tarjeta.

    Returns:
        Lista de IDs ordenados ascendentemente.
    """
    with db_cursor() as cur:
        cur.execute("SELECT id FROM reservations ORDER BY id")
        return [row[0] for row in cur.fetchall()]


def get_vehicles_for_email(email: str) -> list[tuple]:
    """Obtiene los vehículos de un socio para edición de placas.

    Returns:
        Lista de tuplas (id, vehicle, license_plate, service).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, vehicle, license_plate, service "
            "FROM reservations WHERE email = %s ORDER BY created_at DESC",
            (email,),
        )
        return cur.fetchall()
