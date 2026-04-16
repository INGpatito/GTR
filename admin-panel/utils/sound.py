"""
Parking GTR — Sound Effects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Efectos de sonido para Windows (winsound).
Falla silenciosamente en sistemas sin soporte.
"""

import threading

try:
    import winsound
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False


def play_chime() -> None:
    """Toca un chime de bienvenida de lujo (solo Windows).

    Se ejecuta en un hilo separado para no bloquear la UI.
    En sistemas sin soporte de sonido, no hace nada.
    """
    if not _SOUND_AVAILABLE:
        return

    def _play():
        try:
            winsound.Beep(880, 120)
            winsound.Beep(1109, 120)
            winsound.Beep(1318, 200)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
