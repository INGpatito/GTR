"""
Parking GTR — Email Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Envío de correos de aprobación mediante la API REST de EmailJS.
Ejecuta en hilo separado para no bloquear la interfaz.
"""

import threading
from typing import Callable, Optional

import requests

from config.settings import (
    EMAILJS_ACCESS_TOKEN,
    EMAILJS_SERVICE_ID,
    EMAILJS_TEMPLATE_ID,
    EMAILJS_USER_ID,
)

# Tipos para los callbacks
OnSuccess = Callable[[], None]
OnError   = Callable[[str], None]


def send_approval_email(
    to_name: str,
    to_email: str,
    membership_type: str,
    on_success: Optional[OnSuccess] = None,
    on_error: Optional[OnError] = None,
) -> None:
    """Envía un correo de aprobación de membresía via EmailJS.

    Se ejecuta en un hilo separado para no congelar la UI.

    Args:
        to_name: Nombre del destinatario.
        to_email: Dirección de correo del destinatario.
        membership_type: Tipo de membresía (ej. "VALET", "MONTHLY").
        on_success: Callback invocado si el envío fue exitoso.
        on_error: Callback invocado con el mensaje de error si falla.
    """

    def _send():
        try:
            payload = {
                "service_id":  EMAILJS_SERVICE_ID,
                "template_id": EMAILJS_TEMPLATE_ID,
                "user_id":     EMAILJS_USER_ID,
                "accessToken": EMAILJS_ACCESS_TOKEN,
                "template_params": {
                    "to_name":         to_name,
                    "to_email":        to_email,
                    "membership_type": membership_type,
                },
            }

            response = requests.post(
                "https://api.emailjs.com/api/v1.0/email/send",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )

            if response.status_code == 200:
                if on_success:
                    on_success()
            else:
                msg = f"Código: {response.status_code}\n{response.text}"
                if on_error:
                    on_error(msg)

        except Exception as exc:
            if on_error:
                on_error(str(exc))

    threading.Thread(target=_send, daemon=True).start()
