import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from datetime import date
from config.config import FOOTBALL_API_KEY, FOOTBALL_API_BASE_URL, API_RATE_LIMIT_DELAY, TARGET_COMPETITION, DATA_LAKE_RAW_API

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}


def appel_api(endpoint):
    """Appelle l'API et retourne les données JSON."""
    url = f"{FOOTBALL_API_BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Erreur {response.status_code} sur {url}")
        return None

    time.sleep(API_RATE_LIMIT_DELAY)  # respect du rate limit
    return response.json()


def sauvegarder(data, nom_fichier):
    """Sauvegarde les données JSON dans le Data Lake."""
    os.makedirs(DATA_LAKE_RAW_API, exist_ok=True)
    chemin = f"{DATA_LAKE_RAW_API}/{nom_fichier}_{date.today()}.json"

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Sauvegardé : {chemin}")


def collecter_competitions():
    data = appel_api("/competitions")
    if data:
        sauvegarder(data, "competitions")
    return data


def collecter_classement(code=TARGET_COMPETITION):
    data = appel_api(f"/competitions/{code}/standings")
    if data:
        sauvegarder(data, f"standings_{code}")
    return data


def collecter_matchs(code=TARGET_COMPETITION):
    data = appel_api(f"/competitions/{code}/matches")
    if data:
        sauvegarder(data, f"matches_{code}")
    return data


def collecter_equipes(code=TARGET_COMPETITION):
    data = appel_api(f"/competitions/{code}/teams")
    if data:
        sauvegarder(data, f"teams_{code}")
    return data


def collecter_buteurs(code=TARGET_COMPETITION):
    data = appel_api(f"/competitions/{code}/scorers")
    if data:
        sauvegarder(data, f"scorers_{code}")
    return data


if __name__ == "__main__":
    print("=== Collecte API football-data.org ===")
    collecter_classement()
    collecter_matchs()
    collecter_equipes()
    collecter_buteurs()
    print("=== Collecte terminée ===")
