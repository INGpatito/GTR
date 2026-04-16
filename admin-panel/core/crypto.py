"""
Parking GTR — Cryptography Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generación de números de tarjeta HMAC y hashing de contraseñas.
"""

import hashlib
import hmac

import bcrypt

from config.settings import JWT_SECRET


# ══════════════════════════════════════════════════════
#  HMAC — Replica la misma lógica que backend/server.js
# ══════════════════════════════════════════════════════
def generate_card_number(member_id: int) -> str:
    """Genera el número cifrado de 16 dígitos idéntico al backend Node.js.

    Args:
        member_id: ID del socio en la base de datos.

    Returns:
        Número de tarjeta formateado como ``"XXXX XXXX XXXX XXXX"``.
    """
    msg = f"GTR-CARD-{member_id}".encode()
    key = JWT_SECRET.encode()
    hex_digest = hmac.new(key, msg, hashlib.sha256).hexdigest()  # 64 hex chars

    digits = ""
    i = 0
    while len(digits) < 16 and i < 48:
        num = int(hex_digest[i : i + 3], 16) % 10
        digits += str(num)
        i += 3
    while len(digits) < 16:
        digits += "0"

    return f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"


# ══════════════════════════════════════════════════════
#  BCRYPT — Hashing de contraseñas
# ══════════════════════════════════════════════════════
def hash_password(plain_text: str) -> str:
    """Genera un hash bcrypt con 12 rondas de sal.

    Args:
        plain_text: Contraseña en texto plano.

    Returns:
        Hash bcrypt como string UTF-8.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_text.encode("utf-8"), salt).decode("utf-8")
