"""
Parking GTR — Parking Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre las tablas ``parking_spots`` y ``parking_requests``.
Gestiona los 24 espacios de estacionamiento divididos en 3 pisos.
"""

from core.database import db_cursor


# ══════════════════════════════════════════════════════
#  PARKING SPOTS
# ══════════════════════════════════════════════════════

def get_all_spots() -> list[tuple]:
    """Obtiene todos los spots de estacionamiento (excluye helicóptero floor=0).

    Returns:
        Lista de tuplas (id, spot_number, floor, spot_label, status,
                         occupied_by_user_id, occupied_by_vehicle_id, occupied_at,
                         user_name, vehicle_nickname, brand, model, plate).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT ps.id, ps.spot_number, ps.floor, ps.spot_label, ps.status,
                   ps.occupied_by_user_id, ps.occupied_by_vehicle_id, ps.occupied_at,
                   u.full_name AS user_name,
                   uv.nickname AS vehicle_nickname, uv.brand, uv.model, uv.plate
            FROM parking_spots ps
            LEFT JOIN users u ON ps.occupied_by_user_id = u.id
            LEFT JOIN user_vehicles uv ON ps.occupied_by_vehicle_id = uv.id
            WHERE ps.floor > 0
            ORDER BY ps.floor, ps.spot_number
        """)
        return cur.fetchall()


def get_spots_by_floor(floor: int) -> list[tuple]:
    """Obtiene los spots de un piso específico.

    Returns:
        Lista de tuplas con misma estructura que get_all_spots().
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT ps.id, ps.spot_number, ps.floor, ps.spot_label, ps.status,
                   ps.occupied_by_user_id, ps.occupied_by_vehicle_id, ps.occupied_at,
                   u.full_name AS user_name,
                   uv.nickname AS vehicle_nickname, uv.brand, uv.model, uv.plate
            FROM parking_spots ps
            LEFT JOIN users u ON ps.occupied_by_user_id = u.id
            LEFT JOIN user_vehicles uv ON ps.occupied_by_vehicle_id = uv.id
            WHERE ps.floor = %s
            ORDER BY ps.spot_number
        """, (floor,))
        return cur.fetchall()


def get_available_spots(floor: int = None) -> list[tuple]:
    """Obtiene los spots disponibles, opcionalmente filtrados por piso.

    Returns:
        Lista de tuplas (id, spot_number, floor, spot_label).
    """
    with db_cursor() as cur:
        if floor:
            cur.execute("""
                SELECT id, spot_number, floor, spot_label
                FROM parking_spots
                WHERE status = 'available' AND floor = %s
                ORDER BY spot_number
            """, (floor,))
        else:
            cur.execute("""
                SELECT id, spot_number, floor, spot_label
                FROM parking_spots
                WHERE status = 'available' AND floor > 0
                ORDER BY floor, spot_number
            """)
        return cur.fetchall()


def occupy_spot(spot_id: int, user_id: int, vehicle_id: int = None) -> bool:
    """Ocupa un spot de estacionamiento.

    Returns:
        True si se ocupó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute("""
            UPDATE parking_spots
            SET status = 'occupied',
                occupied_by_user_id = %s,
                occupied_by_vehicle_id = %s,
                occupied_at = NOW()
            WHERE id = %s AND status = 'available'
        """, (user_id, vehicle_id, spot_id))
        return cur.rowcount > 0


def free_spot(spot_id: int) -> bool:
    """Libera un spot de estacionamiento.

    Returns:
        True si se liberó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute("""
            UPDATE parking_spots
            SET status = 'available',
                occupied_by_user_id = NULL,
                occupied_by_vehicle_id = NULL,
                occupied_at = NULL
            WHERE id = %s
        """, (spot_id,))
        return cur.rowcount > 0


def free_user_spots(user_id: int) -> int:
    """Libera todos los spots ocupados por un usuario.

    Returns:
        Cantidad de spots liberados.
    """
    with db_cursor() as cur:
        cur.execute("""
            UPDATE parking_spots
            SET status = 'available',
                occupied_by_user_id = NULL,
                occupied_by_vehicle_id = NULL,
                occupied_at = NULL
            WHERE occupied_by_user_id = %s AND status = 'occupied'
        """, (user_id,))
        return cur.rowcount


def get_user_occupied_spots(user_id: int) -> list[tuple]:
    """Obtiene los spots ocupados por un usuario.

    Returns:
        Lista de tuplas (spot_id, spot_label, floor, vehicle_nickname, plate).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT ps.id, ps.spot_label, ps.floor,
                   uv.nickname, uv.plate
            FROM parking_spots ps
            LEFT JOIN user_vehicles uv ON ps.occupied_by_vehicle_id = uv.id
            WHERE ps.occupied_by_user_id = %s AND ps.status = 'occupied'
            ORDER BY ps.floor, ps.spot_number
        """, (user_id,))
        return cur.fetchall()


# ══════════════════════════════════════════════════════
#  PARKING REQUESTS
# ══════════════════════════════════════════════════════

def create_request(user_id: int, vehicle_id: int, request_type: str) -> tuple:
    """Crea una solicitud de parking y cancela las anteriores pendientes.

    Returns:
        Tupla con los datos de la solicitud creada.
    """
    with db_cursor() as cur:
        # Cancelar solicitudes pendientes previas
        cur.execute(
            "UPDATE parking_requests SET status = 'rejected' WHERE user_id = %s AND status = 'pending'",
            (user_id,),
        )
        cur.execute("""
            INSERT INTO parking_requests (user_id, vehicle_id, request_type)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, vehicle_id, request_type, status, created_at
        """, (user_id, vehicle_id, request_type))
        return cur.fetchone()


def get_pending_requests() -> list[tuple]:
    """Obtiene todas las solicitudes pendientes.

    Returns:
        Lista de tuplas (id, user_id, vehicle_id, request_type, status, created_at,
                         full_name, email, vehicle_nickname, brand, model, plate, vehicle_type).
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT pr.id, pr.user_id, pr.vehicle_id, pr.request_type, pr.status, pr.created_at,
                   u.full_name, u.email,
                   uv.nickname AS vehicle_nickname, uv.brand, uv.model, uv.plate, uv.vehicle AS vehicle_type
            FROM parking_requests pr
            JOIN users u ON pr.user_id = u.id
            LEFT JOIN user_vehicles uv ON pr.vehicle_id = uv.id
            WHERE pr.status = 'pending'
            ORDER BY pr.created_at ASC
        """)
        return cur.fetchall()


def approve_request(request_id: int, spot_id: int = None) -> bool:
    """Aprueba una solicitud de parking.

    Para check_in: ocupa el spot indicado.
    Para check_out: libera los spots del usuario.

    Returns:
        True si se aprobó exitosamente.
    """
    with db_cursor() as cur:
        # Obtener la solicitud
        cur.execute(
            "SELECT user_id, vehicle_id, request_type FROM parking_requests WHERE id = %s AND status = 'pending'",
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return False

        user_id, vehicle_id, request_type = row

        if request_type == "check_in":
            if not spot_id:
                return False
            # Verificar disponibilidad
            cur.execute(
                "SELECT id FROM parking_spots WHERE id = %s AND status = 'available'",
                (spot_id,),
            )
            if not cur.fetchone():
                return False
            # Ocupar el spot
            cur.execute("""
                UPDATE parking_spots
                SET status = 'occupied', occupied_by_user_id = %s,
                    occupied_by_vehicle_id = %s, occupied_at = NOW()
                WHERE id = %s
            """, (user_id, vehicle_id, spot_id))

        elif request_type == "check_out":
            # Liberar spots del usuario
            cur.execute("""
                UPDATE parking_spots
                SET status = 'available', occupied_by_user_id = NULL,
                    occupied_by_vehicle_id = NULL, occupied_at = NULL
                WHERE occupied_by_user_id = %s AND status = 'occupied'
            """, (user_id,))

        # Actualizar solicitud
        cur.execute(
            "UPDATE parking_requests SET status = 'approved', spot_id = %s WHERE id = %s",
            (spot_id, request_id),
        )
        return True


def reject_request(request_id: int) -> bool:
    """Rechaza una solicitud de parking.

    Returns:
        True si se rechazó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute(
            "UPDATE parking_requests SET status = 'rejected' WHERE id = %s AND status = 'pending'",
            (request_id,),
        )
        return cur.rowcount > 0


def get_request_status(user_id: int) -> tuple | None:
    """Obtiene el estado de la última solicitud de un usuario.

    Returns:
        Tupla (id, request_type, status, spot_id, created_at) o None.
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, request_type, status, spot_id, created_at
            FROM parking_requests
            WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        return cur.fetchone()
