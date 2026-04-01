import os
# Force la locale anglaise pour éviter que libpq lise des fichiers de messages
# en français (latin-1) depuis l'installation PostgreSQL locale Windows
os.environ["LC_ALL"] = "C"
os.environ["LC_MESSAGES"] = "C"
os.environ["LANG"] = "C"
os.environ["PGPASSFILE"] = "C:/nonexistent_pgpass"

from ingestion.api_client import (
    collecter_classement, collecter_matchs,
    collecter_equipes, collecter_buteurs
)
from ingestion.scraper import scraper_valeurs_marche
from transformation.transform_api import (
    transformer_classement, transformer_matchs,
    transformer_equipes, transformer_buteurs
)
from transformation.transform_scraped import transformer_valeurs_marche
from warehouse.load import (
    charger_competition, charger_equipes, charger_classement,
    charger_matchs, charger_buteurs, charger_valeurs_marche
)

if __name__ == "__main__":
    print("\n=== 1. INGESTION ===")
    raw_standings = collecter_classement()
    raw_equipes   = collecter_equipes()
    raw_matchs    = collecter_matchs()
    raw_buteurs   = collecter_buteurs()
    raw_scraping  = scraper_valeurs_marche()

    print("\n=== 2. TRANSFORMATION ===")
    df_standings = transformer_classement(raw_standings)
    df_equipes   = transformer_equipes(raw_equipes)
    df_matchs    = transformer_matchs(raw_matchs)
    df_buteurs   = transformer_buteurs(raw_buteurs)
    df_market    = transformer_valeurs_marche(raw_scraping)

    print("\n=== 3. CHARGEMENT EN BASE ===")
    charger_competition(raw_standings)
    charger_equipes(df_equipes)
    charger_classement(df_standings)
    charger_matchs(df_matchs)
    charger_buteurs(df_buteurs)
    charger_valeurs_marche(df_market, df_equipes)

    print("\n=== Pipeline terminé ===")
