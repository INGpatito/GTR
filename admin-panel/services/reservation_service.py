"""
Parking GTR — Reservation Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones CRUD sobre la tabla ``reservations``.
"""

from psycopg2 import Error as PGError

from core.database import db_cursor


def get_all_reservations(pending_only: bool = False) -> list[tuple]:
    """Obtiene todas las reservaciones, opcionalmente filtradas por pendientes.

    Args:
        pending_only: Si True, retorna solo registros con status 'pending' o NULL.

    Returns:
        Lista de tuplas (id, full_name, service, vehicle, arrival_date, arrival_time, status).
    """
    with db_cursor() as cur:
        if pending_only:
            cur.execute(
                "SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status "
                "FROM reservations WHERE status = 'pending' OR status IS NULL "
                "ORDER BY created_at DESC;"
            )
        else:
            cur.execute(
                "SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status "
                "FROM reservations ORDER BY created_at DESC;"
            )
        return cur.fetchall()


def get_reservation_by_id(record_id: int) -> tuple | None:
    """Obtiene una reservación por su ID.

    Returns:
        Tupla (id, full_name, email, phone, service, vehicle,
               arrival_date, arrival_time, status, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, full_name, email, phone, service, vehicle, "
            "arrival_date, arrival_time, status, created_at "
            "FROM reservations WHERE id = %s",
            (record_id,),
        )
        return cur.fetchone()


def get_user_info_for_approval(record_id: int) -> tuple | None:
    """Obtiene datos mínimos del usuario para enviar correo de aprobación.

    Returns:
        Tupla (full_name, email, service) o None.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT full_name, email, service FROM reservations WHERE id = %s",
            (record_id,),
        )
        return cur.fetchone()


def mark_completed(record_id: int) -> None:
    """Marca una reservación como 'completed'."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE reservations SET status = %s WHERE id = %s",
            ("completed", record_id),
        )


def update_status(record_id: int, new_status: str) -> None:
    """Actualiza el status de una reservación.

    Args:
        record_id: ID de la reservación.
        new_status: Nuevo estado ('pending', 'confirmed', 'completed').
    """
    with db_cursor() as cur:
        cur.execute(
            "UPDATE reservations SET status = %s WHERE id = %s",
            (new_status, record_id),
        )


def delete_reservation(record_id: int) -> None:
    """Elimina una reservación por su ID."""
    with db_cursor() as cur:
        cur.execute("DELETE FROM reservations WHERE id = %s", (record_id,))
