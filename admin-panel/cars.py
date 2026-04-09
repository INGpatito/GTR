import os
import requests
from dotenv import load_dotenv

load_dotenv()

def obtener_foto_carro(placa, estado):
    api_key = os.getenv("CARSXE_API_KEY")
    if not api_key:
        print("⚠️ CARSXE_API_KEY not found in .env")
        return None
    
    # URL del endpoint de imágenes
    url = "https://api.carsxe.com/images"
    
    # Parámetros de la consulta
    params = {
        "key": api_key,
        "plate": placa,
        "state": estado, # Ej: 'MX' o el estado específico si es de USA
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            # CarsXE devuelve una lista de imágenes
            imagenes = data.get("images", [])
            if imagenes:
                print(f"✅ ¡Carro encontrado para la placa {placa}!")
                # Tomamos la primera URL de la lista
                foto_url = imagenes[0].get("url")
                print(f"📸 URL de la foto: {foto_url}")
                return foto_url
            else:
                print("❌ No se encontraron imágenes para esa placa.")
        else:
            print(f"⚠️ Error de la API: {data.get('error', 'Desconocido')}")
            
    except Exception as e:
        print(f"🔥 Error de conexión: {e}")

# --- PRUEBA DEL SCRIPT ---
# Ejemplo: Placa de prueba (Asegúrate de que sea una válida para el país/estado)
mi_placa = "ABC1234" 
mi_estado = "CA" # O el código de país según la doc de CarsXE

foto = obtener_foto_carro(mi_placa, mi_estado)