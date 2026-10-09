
import requests
import pandas as pd
import time
import json
from pathlib import Path

# Link de la API de Steam para obtener reseñas de Firewatch
url = "https://store.steampowered.com/appreviews/383870"

archivo = Path("firewatch_reviews.csv")
progreso = Path("progreso.json")

# Cantidad máxima de reseñas 
limite = 60000
cursor = "*"

# Progreso previo (para los timeouts de Steam)
if progreso.exists():
    with open(progreso, "r") as f:
        estado = json.load(f)
    cursor = estado["cursor"]
    print("Continuando extracción")

# ID de reseñas ya descargadas
ids = set()

if archivo.exists():
    anteriores = pd.read_csv(
        archivo,
        usecols=["recommendationid"]
    )
    ids = set(anteriores["recommendationid"].astype(str))

print("Reseñas guardadas:", len(ids))

while len(ids) < limite:

    params = {
        "json": 1,
        "language": "english",
        "filter": "recent",
        "num_per_page": 100,
        "cursor": cursor
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 429:
            print("Límite de Steam alcanzado.")
            print("Guardando progreso. Intentar más tarde.")
            break

        response.raise_for_status()
        data = response.json()

        nuevas = data["reviews"]

        if not nuevas:
            print("No hay más reseñas disponibles.")
            break

        # Evitar duplicados
        unicas = []

        for review in nuevas:
            review_id = str(review["recommendationid"])

            if review_id not in ids:
                unicas.append(review)
                ids.add(review_id)

        # Guardar las nuevas reseñas
        if unicas:
            df = pd.json_normalize(unicas)

            df.to_csv(
                archivo,
                mode="a",
                header=not archivo.exists(),
                index=False
            )

        # Guardar cursor para continuar
        cursor = data["cursor"]

        with open(progreso, "w") as f:
            json.dump({"cursor": cursor}, f)

        print("Reseñas descargadas:", len(ids))

        time.sleep(10)

    except requests.RequestException as e:
        print("Error de conexión:", e)
        print("Continuar más tarde.")
        break

print("Extracción finalizada.")
print("Total de reseñas:", len(ids))
