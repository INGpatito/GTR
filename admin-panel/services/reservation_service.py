"""
Parking GTR — Reservation Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones CRUD sobre las tablas ``reservations`` y ``users``.
"""

from psycopg2 import Error as PGError

from core.database import db_cursor


def get_all_reservations(pending_only: bool = False) -> list[tuple]:
    """Obtiene todas las reservaciones con datos del usuario.

    Args:
        pending_only: Si True, retorna solo registros con status 'pending' o NULL.

    Returns:
        Lista de tuplas (id, full_name, service, vehicle, arrival_date, arrival_time, status).
    """
    with db_cursor() as cur:
        if pending_only:
            cur.execute(
                "SELECT r.id, u.full_name, r.service, r.vehicle, "
                "r.arrival_date, r.arrival_time, r.status "
                "FROM reservations r "
                "JOIN users u ON r.user_id = u.id "
                "WHERE r.status = 'pending' OR r.status IS NULL "
                "ORDER BY r.created_at DESC;"
            )
        else:
            cur.execute(
                "SELECT r.id, u.full_name, r.service, r.vehicle, "
                "r.arrival_date, r.arrival_time, r.status "
                "FROM reservations r "
                "JOIN users u ON r.user_id = u.id "
                "ORDER BY r.created_at DESC;"
            )
        return cur.fetchall()


def get_reservation_by_id(record_id: int) -> tuple | None:
    """Obtiene una reservación por su ID con datos del usuario.

    Returns:
        Tupla (id, full_name, email, phone, service, vehicle,
               arrival_date, arrival_time, status, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT r.id, u.full_name, u.email, u.phone, r.service, r.vehicle, "
            "r.arrival_date, r.arrival_time, r.status, r.created_at "
            "FROM reservations r "
            "JOIN users u ON r.user_id = u.id "
            "WHERE r.id = %s",
            (record_id,),
        )
        return cur.fetchone()


def get_user_info_for_approval(record_id: int) -> tuple | None:
    """Obtiene datos mínimos del usuario para enviar correo de aprobación.

    Returns:
        Tupla (full_name, email, service, user_id) o None.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT u.full_name, u.email, r.service, r.user_id "
            "FROM reservations r "
            "JOIN users u ON r.user_id = u.id "
            "WHERE r.id = %s",
            (record_id,),
        )
        return cur.fetchone()


def mark_completed(record_id: int) -> None:
    """Marca una reservación como 'completed' y activa al usuario.
    
    Actualiza tanto el status de la reservación como el status del
    usuario en la tabla users para permitir el inicio de sesión.
    """
    with db_cursor() as cur:
        # 1. Marcar la reservación como completada
        cur.execute(
            "UPDATE reservations SET status = %s WHERE id = %s",
            ("completed", record_id),
        )
        # 2. Activar al usuario en la tabla users para permitir login
        cur.execute(
            "UPDATE users SET status = 'active' "
            "WHERE id = (SELECT user_id FROM reservations WHERE id = %s)",
            (record_id,),
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
