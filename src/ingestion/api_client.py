import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from config.config import FOOTBALL_API_KEY, FOOTBALL_API_BASE_URL, API_RATE_LIMIT_DELAY, TARGET_COMPETITION

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}


def appel_api(endpoint):
    """Appelle l'API et retourne les données JSON."""
    url = f"{FOOTBALL_API_BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Erreur {response.status_code} sur {url}")
        return None

    time.sleep(API_RATE_LIMIT_DELAY)
    return response.json()


def collecter_classement(code=TARGET_COMPETITION):
    print(f"Collecte classement {code}...")
    return appel_api(f"/competitions/{code}/standings")


def collecter_matchs(code=TARGET_COMPETITION):
    print(f"Collecte matchs {code}...")
    return appel_api(f"/competitions/{code}/matches")


def collecter_equipes(code=TARGET_COMPETITION):
    print(f"Collecte équipes {code}...")
    return appel_api(f"/competitions/{code}/teams")


def collecter_buteurs(code=TARGET_COMPETITION):
    print(f"Collecte buteurs {code}...")
    return appel_api(f"/competitions/{code}/scorers")
