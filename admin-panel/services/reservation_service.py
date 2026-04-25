"""
Parking GTR — Reservation Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones CRUD sobre la tabla ``reservations``, unida a ``users``.
"""

from psycopg2 import Error as PGError
from core.database import db_cursor


def get_all_reservations(pending_only: bool = False) -> list[tuple]:
    """Obtiene todas las reservaciones, unidas con datos de usuario.

    Args:
        pending_only: Si True, retorna solo registros con status 'pending' o NULL.

    Returns:
        Lista de tuplas (id, full_name, service, vehicle, arrival_date, arrival_time, status).
    """
    with db_cursor() as cur:
        query = """
            SELECT r.id, u.full_name, r.service, r.vehicle, r.arrival_date, r.arrival_time, r.status
            FROM reservations r
            JOIN users u ON r.user_id = u.id
        """
        if pending_only:
            query += " WHERE r.status = 'pending' OR r.status IS NULL "
        
        query += " ORDER BY r.created_at DESC;"
        
        cur.execute(query)
        return cur.fetchall()


def get_reservation_by_id(record_id: int) -> tuple | None:
    """Obtiene una reservación por su ID, con datos de usuario.

    Returns:
        Tupla (id, full_name, email, phone, service, vehicle,
               arrival_date, arrival_time, status, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT r.id, u.full_name, u.email, u.phone, r.service, r.vehicle,
                   r.arrival_date, r.arrival_time, r.status, r.created_at
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """, (record_id,))
        return cur.fetchone()


def get_user_info_for_approval(record_id: int) -> tuple | None:
    """Obtiene datos del usuario para enviar correo de aprobación."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.full_name, u.email, r.service 
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """, (record_id,))
        return cur.fetchone()


def mark_completed(record_id: int) -> None:
    """Marca una reservación como 'completed' y asegura que el usuario sea 'active'."""
    with db_cursor() as cur:
        # 1. Marcar reservación como completada
        cur.execute(
            "UPDATE reservations SET status = %s WHERE id = %s RETURNING user_id",
            ("completed", record_id),
        )
        res = cur.fetchone()
        
        # 2. Asegurar que el usuario esté activo
        if res:
            user_id = res[0]
            cur.execute(
                "UPDATE users SET status = 'active' WHERE id = %s",
                (user_id,)
            )


def update_status(record_id: int, new_status: str) -> None:
    """Actualiza el status de una reservación."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE reservations SET status = %s WHERE id = %s",
            (new_status, record_id),
        )


def delete_reservation(record_id: int) -> None:
    """Elimina una reservación por su ID."""
    with db_cursor() as cur:
        cur.execute("DELETE FROM reservations WHERE id = %s", (record_id,))
