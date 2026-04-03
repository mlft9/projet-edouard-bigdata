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
from transformation.merge import NOM_TRANSFERMARKT_VERS_API
from ingestion.kafka_producer import creer_producer, envoyer_messages

if __name__ == "__main__":
    try:
        # ── 1. INGESTION ─────────────────────────────────────────────
        print("\n=== 1. INGESTION ===")
        raw_standings = collecter_classement()
        raw_equipes   = collecter_equipes()
        raw_matchs    = collecter_matchs()
        raw_buteurs   = collecter_buteurs()
        raw_scraping  = scraper_valeurs_marche()

        if not all([raw_standings, raw_equipes, raw_matchs, raw_buteurs]):
            print("Erreur : certaines données API sont manquantes. Arrêt du pipeline.")
            exit(1)

        # ── 2. TRANSFORMATION ────────────────────────────────────────
        print("\n=== 2. TRANSFORMATION ===")
        df_standings = transformer_classement(raw_standings)
        df_equipes   = transformer_equipes(raw_equipes)
        df_matchs    = transformer_matchs(raw_matchs)
        df_buteurs   = transformer_buteurs(raw_buteurs)
        df_market    = transformer_valeurs_marche(raw_scraping)

        # ── 3. ENVOI VERS KAFKA ──────────────────────────────────────
        print("\n=== 3. ENVOI VERS KAFKA ===")
        producer = creer_producer()

        # Compétition : un seul enregistrement extrait du JSON brut
        comp = raw_standings["competition"]
        envoyer_messages(producer, "competition", [{
            "id":   comp["id"],
            "name": comp["name"],
            "code": comp["code"],
            "area": raw_standings["area"]["name"],
            "type": comp["type"],
        }])

        envoyer_messages(producer, "teams",     df_equipes.to_dict("records"))
        envoyer_messages(producer, "standings", df_standings.to_dict("records"))
        envoyer_messages(producer, "matches",   df_matchs.to_dict("records"))
        envoyer_messages(producer, "scorers",   df_buteurs.to_dict("records"))

        # Valeurs marchandes : résolution nom → team_id avant envoi
        nom_vers_id = dict(zip(df_equipes["name"], df_equipes["id"]))
        market_records = []
        for r in df_market.to_dict("records"):
            nom_api = NOM_TRANSFERMARKT_VERS_API.get(r["team_name"], r["team_name"])
            team_id = nom_vers_id.get(nom_api)
            if team_id:
                market_records.append({
                    "team_id":        team_id,
                    "season":         "2025",
                    "squad_size":     r.get("squad_size"),
                    "avg_age":        r.get("avg_age"),
                    "foreigners":     r.get("foreigners"),
                    "market_value_m": r.get("market_value_m"),
                })
        envoyer_messages(producer, "market_values", market_records)

        producer.close()
        print("\n=== Messages envoyés vers Kafka. Lancez spark_job.py pour charger en base. ===")

    except Exception as e:
        print(f"\nErreur pipeline : {e}")
        exit(1)
