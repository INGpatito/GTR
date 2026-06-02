"""
Parking GTR — Vehicle Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Consultas sobre la tabla ``user_vehicles`` y actividad.
Usado principalmente por Member Scanner.
"""

from core.database import db_cursor


def get_user_vehicles(user_id: int) -> list[tuple]:
    """Obtiene los vehículos registrados de un socio.

    Returns:
        Lista de tuplas (nickname, vehicle, brand, model, year, color, plate, is_primary).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT nickname, vehicle, brand, model, year, color, plate, is_primary "
            "FROM user_vehicles WHERE user_id = %s "
            "ORDER BY is_primary DESC, created_at ASC",
            (user_id,),
        )
        return cur.fetchall()


def get_activity_history(user_id: int, limit: int = 10) -> list[tuple]:
    """Obtiene el historial de actividad reciente de un socio.

    Args:
        user_id: ID del socio en la tabla users.
        limit: Número máximo de registros a retornar.

    Returns:
        Lista de tuplas (service, status, created_at).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT service, status, created_at "
            "FROM reservations "
            "WHERE user_id = %s "
            "ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return cur.fetchall()
