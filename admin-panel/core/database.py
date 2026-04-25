"""
Parking GTR — Database Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provee conexión centralizada a PostgreSQL con pool de conexiones
para manejo eficiente y auto-commit.
"""

from contextlib import contextmanager

from psycopg2 import Error as PGError
from psycopg2.pool import ThreadedConnectionPool

from config.settings import DB_PARAMS

# Crear un pool global. Mínimo 1 conexión, máximo 5 conexiones.
try:
    _pool = ThreadedConnectionPool(1, 5, **DB_PARAMS)
except PGError as e:
    print(f"Error inicializando Connection Pool: {e}")
    _pool = None

def get_connection():
    """Obtiene y retorna una conexión a PostgreSQL desde el pool.

    Returns:
        psycopg2.connection | None: Conexión activa, o None si falla.
    """
    if _pool:
        try:
            return _pool.getconn()
        except PGError:
            return None
    return None

def put_connection(conn):
    """Devuelve la conexión al pool."""
    if _pool and conn:
        _pool.putconn(conn)

@contextmanager
def db_cursor():
    """Context manager que provee un cursor con auto-commit y cleanup.

    Uso::

        with db_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
        # Conexión devuelta al pool y cursor cerrado automáticamente

    Raises:
        PGError: Si no se puede conectar a la base de datos.
    """
    if not _pool:
        raise PGError("Database pool is not initialized")
        
    conn = _pool.getconn()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        _pool.putconn(conn)
