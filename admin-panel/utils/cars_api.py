"""
Parking GTR — CarsXE API Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Consulta la API de CarsXE para obtener imágenes de vehículos por matrícula.
"""

import requests

from config.settings import CARSXE_API_KEY


def obtener_foto_carro(placa: str, estado: str) -> str | None:
    """Busca una foto del vehículo por su matrícula via CarsXE.

    Args:
        placa: Número de matrícula del vehículo.
        estado: Código de estado/país (ej. 'CA', 'MX').

    Returns:
        URL de la primera imagen encontrada, o None si no hay resultados.
    """
    if not CARSXE_API_KEY:
        print("⚠️ CARSXE_API_KEY not found in .env")
        return None

    url = "https://api.carsxe.com/images"
    params = {
        "key":    CARSXE_API_KEY,
        "plate":  placa,
        "state":  estado,
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            imagenes = data.get("images", [])
            if imagenes:
                foto_url = imagenes[0].get("url")
                print(f"✅ Carro encontrado para la placa {placa}")
                print(f"📸 URL de la foto: {foto_url}")
                return foto_url
            else:
                print("❌ No se encontraron imágenes para esa placa.")
        else:
            print(f"⚠️ Error de la API: {data.get('error', 'Desconocido')}")

    except Exception as exc:
        print(f"🔥 Error de conexión: {exc}")

    return None
