"""
Parking GTR — Database Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provee conexión centralizada a PostgreSQL con context manager
para manejo automático de cursor y conexión.
"""

from contextlib import contextmanager

import psycopg2
from psycopg2 import Error as PGError

from config.settings import DB_PARAMS


def get_connection():
    """Crea y retorna una nueva conexión a PostgreSQL.

    Returns:
        psycopg2.connection | None: Conexión activa, o None si falla.
    """
    try:
        return psycopg2.connect(**DB_PARAMS)
    except PGError:
        return None


@contextmanager
def db_cursor():
    """Context manager que provee un cursor con auto-commit y cleanup.

    Uso::

        with db_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
        # Conexión y cursor se cierran automáticamente

    Raises:
        PGError: Si no se puede conectar a la base de datos.
    """
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
