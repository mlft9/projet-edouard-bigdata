import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
import time
from bs4 import BeautifulSoup

URL_TRANSFERMARKT = "https://www.transfermarkt.com/ligue-1/startseite/wettbewerb/FR1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def scraper_valeurs_marche():
    """Scrape les valeurs marchandes des équipes Ligue 1 depuis transfermarkt.com"""
    print(f"Scraping : {URL_TRANSFERMARKT}")
    try:
        response = requests.get(URL_TRANSFERMARKT, headers=HEADERS)
        if response.status_code != 200:
            print(f"Erreur {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"class": "items"})

        if not table:
            print("Table non trouvée sur la page.")
            return None

        rows = []
        for tr in table.find("tbody").find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 4:
                continue

            team_name = tr.find("td", {"class": "hauptlink"})
            team_name = team_name.get_text(strip=True) if team_name else ""

            squad_size   = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            avg_age      = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            foreigners   = cells[4].get_text(strip=True) if len(cells) > 4 else ""
            market_value = cells[-1].get_text(strip=True) if cells else ""

            if team_name:
                rows.append({
                    "team_name": team_name,
                    "squad_size": squad_size,
                    "avg_age": avg_age,
                    "foreigners": foreigners,
                    "market_value": market_value
                })

        time.sleep(2)
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return None
