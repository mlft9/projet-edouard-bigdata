# Pipeline Big Data — Ligue 1

Pipeline de données complet allant de la collecte à la visualisation, combinant une API REST et du scraping web pour alimenter un Data Warehouse PostgreSQL.

---

## Architecture globale

![Architecture globale](pipeline_architecture_football.svg "Architecture globale")

---

## Flux de données détaillé

```
main.py
  │
  ├── 1. INGESTION
  │     ├── collecter_classement()   → dict JSON  ──┐
  │     ├── collecter_equipes()      → dict JSON    │  données
  │     ├── collecter_matchs()       → dict JSON    │  brutes
  │     ├── collecter_buteurs()      → dict JSON  ──┤  en mémoire
  │     └── scraper_valeurs_marche() → DataFrame  ──┘
  │
  ├── 2. TRANSFORMATION
  │     ├── transformer_classement(raw)  → DataFrame (18 lignes)
  │     ├── transformer_equipes(raw)     → DataFrame (18 lignes)
  │     ├── transformer_matchs(raw)      → DataFrame (306 lignes)
  │     ├── transformer_buteurs(raw)     → DataFrame (10 lignes)
  │     └── transformer_valeurs_marche(raw) → DataFrame (18 lignes)
  │
  └── 3. CHARGEMENT
        ├── charger_competition()   →  1 ligne  dans competitions
        ├── charger_equipes()       → 18 lignes dans teams
        ├── charger_classement()    → 18 lignes dans standings
        ├── charger_matchs()        → 306 lignes dans matches
        ├── charger_buteurs()       → 10 lignes dans scorers
        └── charger_valeurs_marche() → 18 lignes dans team_stats_scraped
```

---

## Schéma de la base de données

```
competitions
┌────┬──────┬──────┬──────┬──────┐
│ id │ name │ code │ area │ type │
└──┬─┴──────┴──────┴──────┴──────┘
   │
   │ 1─────────────────────────────n
   ▼
standings                               matches
┌────┬────────────────┬──────────┬─┐   ┌────┬────────────────┬─────────────┐
│ id │ competition_id │ team_id  │…│   │ id │ competition_id │ home_team_id│
│    │ season         │ position │ │   │    │ matchday        │ away_team_id│
│    │ points         │ played   │ │   │    │ utc_date        │ home_score  │
└────┴────────────────┴────┬─────┴─┘   │    │ status          │ away_score  │
                           │           └────┴────────────────┴─────────────┘
scorers                    │
┌────┬────────────────┬────▼──────┐    team_stats_scraped
│ id │ competition_id │ team_id   │   ┌────┬─────────┬──────────────────────┐
│    │ player_name    │ goals     │   │ id │ team_id │ market_value_m       │
│    │ assists        │ penalties │   │    │ season  │ squad_size  avg_age  │
└────┴────────────────┴───────────┘   └────┴────────-┴──────────────────────┘
                           │                          ▲
                           └──────────────────────────┘
                                     teams
                             ┌────┬──────┬────────────┐
                             │ id │ name │ short_name │
                             │    │ tla  │ founded    │
                             │    │ area │ venue      │
                             └────┴──────┴────────────┘
```

---

## Structure du projet

```
projet/
├── config/
│   └── config.py            # Clé API, connexion DB, paramètres
├── ingestion/
│   ├── api_client.py        # Collecte depuis football-data.org
│   └── scraper.py           # Scraping transfermarkt.com
├── transformation/
│   ├── transform_api.py     # Nettoyage données API → DataFrames
│   ├── transform_scraped.py # Nettoyage données scrapées
│   └── merge.py             # Fusion des deux sources
├── warehouse/
│   ├── schema.sql           # Définition des tables PostgreSQL
│   └── load.py              # Insertion en base
├── dashboard/
│   └── app.py               # Interface Streamlit
├── docker-compose.yml       # PostgreSQL conteneurisé
├── main.py                  # Orchestrateur du pipeline
├── requirements.txt
└── .env                     # Clé API + credentials DB (non versionné)
```

---

## Installation et lancement

### Prérequis
- Python 3.10+
- Docker Desktop

### 1. Cloner et installer les dépendances
```bash
git clone <repo>
cd projet
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec ta clé API et le mot de passe PostgreSQL
```

### 3. Démarrer la base de données
```bash
docker compose up -d
```

### 4. Lancer le pipeline (ingestion → transformation → chargement)
```bash
python main.py
```

### 5. Lancer le dashboard
```bash
streamlit run dashboard/app.py
```

---

## Technologies utilisées

| Rôle | Technologie |
|------|-------------|
| Langage | Python 3.13 |
| Ingestion API | `requests` |
| Scraping web | `requests` + `BeautifulSoup` |
| Transformation | `pandas` |
| Base de données | PostgreSQL 16 (Docker) |
| Driver DB | `pg8000` |
| Visualisation | `Streamlit` + `Plotly` |
| Conteneurisation | Docker Compose |

---

## Données collectées

| Source | Données | Volume |
|--------|---------|--------|
| football-data.org API | Classement, matchs, équipes, buteurs | ~350 lignes |
| transfermarkt.com (scraping) | Valeur marchande, effectif, âge moyen | 18 lignes |
