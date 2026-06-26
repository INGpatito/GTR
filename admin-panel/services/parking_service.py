"""
Parking GTR — Parking Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Operaciones sobre las tablas ``parking_spots`` y ``parking_requests``.
Gestiona los 24 espacios de estacionamiento divididos en 3 pisos
y el helipuerto (floor=0).
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
    """Obtiene los spots de un piso específico."""
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
    """Obtiene los spots disponibles, opcionalmente filtrados por piso."""
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
    
    Si el vehículo ya ocupa otro spot, lo libera primero (reasignación).
    """
    with db_cursor() as cur:
        # Prevent duplicate assignment: free old spot if vehicle already parked
        if vehicle_id:
            cur.execute("""
                UPDATE parking_spots
                SET status = 'available',
                    occupied_by_user_id = NULL,
                    occupied_by_vehicle_id = NULL,
                    occupied_at = NULL
                WHERE occupied_by_vehicle_id = %s AND status = 'occupied' AND id != %s
            """, (vehicle_id, spot_id))
            if cur.rowcount > 0:
                print(f"[PARKING] Vehículo {vehicle_id} reasignado: spot anterior liberado")

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
    """Libera un spot de estacionamiento."""
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
    """Libera todos los spots ocupados por un usuario."""
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
    """Obtiene los spots ocupados por un usuario."""
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
#  HELIPORT
# ══════════════════════════════════════════════════════

def get_heliport_status() -> tuple | None:
    """Obtiene el estado del helipuerto (floor=0, HELI-01).

    Returns:
        Tupla (id, spot_label, status, occupied_by_user_id, occupied_at, user_name) o None.
    """
    with db_cursor() as cur:
        cur.execute("""
            SELECT ps.id, ps.spot_label, ps.status,
                   ps.occupied_by_user_id, ps.occupied_at,
                   u.full_name AS user_name
            FROM parking_spots ps
            LEFT JOIN users u ON ps.occupied_by_user_id = u.id
            WHERE ps.floor = 0 AND ps.spot_label = 'HELI-01'
            LIMIT 1
        """)
        return cur.fetchone()


def reserve_heliport(user_id: int) -> bool:
    """Reserva el helipuerto para un usuario.

    Returns:
        True si se reservó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute("""
            UPDATE parking_spots
            SET status = 'occupied',
                occupied_by_user_id = %s,
                occupied_at = NOW()
            WHERE floor = 0 AND spot_label = 'HELI-01' AND status = 'available'
        """, (user_id,))
        return cur.rowcount > 0


def free_heliport() -> bool:
    """Libera el helipuerto.

    Returns:
        True si se liberó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute("""
            UPDATE parking_spots
            SET status = 'available',
                occupied_by_user_id = NULL,
                occupied_at = NULL
            WHERE floor = 0 AND spot_label = 'HELI-01'
        """)
        return cur.rowcount > 0


# ══════════════════════════════════════════════════════
#  PARKING REQUESTS
# ══════════════════════════════════════════════════════

def create_request(user_id: int, vehicle_id: int, request_type: str) -> tuple:
    """Crea una solicitud de parking y cancela las anteriores pendientes."""
    with db_cursor() as cur:
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
    """Obtiene todas las solicitudes pendientes (incluyendo heliport)."""
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

    Para check_in: simplemente marca como 'approved' sin asignar spot.
                   El usuario elegirá el spot desde Android.
    Para check_out: libera los spots del usuario.
    Para heliport: ocupa el helipuerto.

    Returns:
        True si se aprobó exitosamente.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT user_id, vehicle_id, request_type FROM parking_requests WHERE id = %s AND status = 'pending'",
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return False

        user_id, vehicle_id, request_type = row

        if request_type == "check_in":
            # Approve without assigning spot — user picks from Android
            cur.execute(
                "UPDATE parking_requests SET status = 'approved' WHERE id = %s",
                (request_id,),
            )

        elif request_type == "check_out":
            # Free the user's occupied spots
            cur.execute("""
                UPDATE parking_spots
                SET status = 'available', occupied_by_user_id = NULL,
                    occupied_by_vehicle_id = NULL, occupied_at = NULL
                WHERE occupied_by_user_id = %s AND status = 'occupied'
            """, (user_id,))
            cur.execute(
                "UPDATE parking_requests SET status = 'approved' WHERE id = %s",
                (request_id,),
            )

        elif request_type == "heliport":
            # Reserve the heliport
            cur.execute("""
                UPDATE parking_spots
                SET status = 'occupied', occupied_by_user_id = %s, occupied_at = NOW()
                WHERE floor = 0 AND spot_label = 'HELI-01' AND status = 'available'
            """, (user_id,))
            if cur.rowcount == 0:
                return False
            # Get heliport spot id
            cur.execute("SELECT id FROM parking_spots WHERE floor = 0 AND spot_label = 'HELI-01'")
            heli_row = cur.fetchone()
            heli_id = heli_row[0] if heli_row else None
            cur.execute(
                "UPDATE parking_requests SET status = 'approved', spot_id = %s WHERE id = %s",
                (heli_id, request_id),
            )

        return True


def reject_request(request_id: int) -> bool:
    """Rechaza una solicitud de parking."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE parking_requests SET status = 'rejected' WHERE id = %s AND status = 'pending'",
            (request_id,),
        )
        return cur.rowcount > 0


def get_request_status(user_id: int) -> tuple | None:
    """Obtiene el estado de la última solicitud de un usuario."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, request_type, status, spot_id, created_at
            FROM parking_requests
            WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        return cur.fetchone()
