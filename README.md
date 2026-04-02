# Pipeline Big Data — Ligue 1

Pipeline de données complet : collecte → Kafka → Spark → PostgreSQL → visualisation.  
Combine une API REST et du scraping web pour alimenter un Data Warehouse PostgreSQL.

---

## Architecture globale

![Architecture globale](pipeline_architecture_football.svg "Architecture globale")

---

## Flux de données

```
Python (main.py)
  │
  ├── 1. INGESTION
  │     ├── collecter_classement()    → dict JSON
  │     ├── collecter_equipes()       → dict JSON
  │     ├── collecter_matchs()        → dict JSON
  │     ├── collecter_buteurs()       → dict JSON
  │     └── scraper_valeurs_marche()  → DataFrame
  │
  ├── 2. TRANSFORMATION (pandas)
  │     ├── transformer_classement()  → DataFrame (18 lignes)
  │     ├── transformer_equipes()     → DataFrame (18 lignes)
  │     ├── transformer_matchs()      → DataFrame (306 lignes)
  │     ├── transformer_buteurs()     → DataFrame (10 lignes)
  │     └── transformer_valeurs_marche() → DataFrame (18 lignes)
  │
  └── 3. ENVOI VERS KAFKA (topic: etl_topic)
        ├── competition   →  1 message
        ├── teams         → 18 messages
        ├── standings     → 18 messages
        ├── matches       → 306 messages
        ├── scorers       → 10 messages
        └── market_values → 18 messages

            ↓ Kafka (broker)

Spark (spark_job.py)
  │
  ├── Lecture batch depuis Kafka (etl_topic)
  ├── Tri des messages par type + dédoublonnage
  ├── Sauvegarde dans HDFS (hdfs://namenode:8020/data/raw/)
  │     ├── /data/raw/competition
  │     ├── /data/raw/teams
  │     ├── /data/raw/standings
  │     ├── /data/raw/matches
  │     ├── /data/raw/scorers
  │     └── /data/raw/market_values
  ├── Truncation des tables PostgreSQL (CASCADE)
  └── Chargement via JDBC
        ├── competitions       →  1 ligne
        ├── teams              → 18 lignes
        ├── standings          → 18 lignes
        ├── matches            → 306 lignes
        ├── scorers            → 10 lignes
        └── team_stats_scraped → 18 lignes

            ↓ PostgreSQL

Streamlit (dashboard/app.py)
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
└────┴────────────────┴───────────┘   └────┴─────────┴──────────────────────┘
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
│   └── config.py              # Clé API, connexion DB, config Kafka
├── ingestion/
│   ├── api_client.py          # Collecte depuis football-data.org
│   ├── kafka_producer.py      # Envoi des données vers Kafka
│   └── scraper.py             # Scraping transfermarkt.com
├── transformation/
│   ├── transform_api.py       # Nettoyage données API → DataFrames
│   ├── transform_scraped.py   # Nettoyage données scrapées
│   └── merge.py               # Correspondance noms d'équipes
├── warehouse/
│   ├── schema.sql             # Définition des tables PostgreSQL
│   └── load.py                # Chargement direct (sans Kafka, pour debug)
├── dashboard/
│   └── app.py                 # Interface Streamlit
├── spark_job.py               # Job Spark : lit Kafka → HDFS + PostgreSQL
├── docker-compose.yml         # Zookeeper, Kafka, PostgreSQL, Spark, HDFS
├── main.py                    # Orchestrateur : ingestion → transformation → Kafka
├── requirements.txt
└── .env                       # Clé API + credentials DB (non versionné)
```

---

## Installation

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
# Renseigner la clé API football-data.org dans .env
```

---

## Lancement du pipeline

### 1. Démarrer l'infrastructure Docker
```bash
docker compose up -d
```
Attendre ~20 secondes que Kafka soit prêt.

### 2. Lancer le pipeline Python (producteur Kafka)
```bash
python main.py
```
Collecte les données, les transforme, et les envoie vers le topic Kafka `etl_topic`.

### 3. Lancer le job Spark (consommateur → PostgreSQL)

Première fois uniquement :
```bash
docker exec -u root spark-master pip install psycopg2-binary -q
```

Puis lancer le job (sur une seule ligne) :
```bash
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 /opt/spark-apps/spark_job.py
```
Le premier lancement télécharge les JARs Kafka et PostgreSQL (~1 min). Les suivants sont instantanés.

### 4. Lancer le dashboard
```bash
streamlit run dashboard/app.py
```

---

## Vérification des données

```bash
# Se connecter à PostgreSQL
docker exec -it postgres psql -U postgres -d football_dw

# Vérifier les données
SELECT COUNT(*) FROM teams;
SELECT COUNT(*) FROM matches;
SELECT position, team_name, points FROM standings ORDER BY position LIMIT 5;
\q
```

---

## Interfaces web

| Service | URL |
|---------|-----|
| Spark UI | http://localhost:8080 |
| HDFS Namenode UI | http://localhost:9870 |
| Dashboard Streamlit | http://localhost:8501 |

---

## Technologies utilisées

| Rôle | Technologie |
|------|-------------|
| Langage | Python 3.13 |
| Ingestion API | `requests` |
| Scraping web | `requests` + `BeautifulSoup` |
| Transformation | `pandas` |
| Message broker | Apache Kafka (Confluent 7.6) |
| Traitement distribué | Apache Spark 3.5 |
| Base de données | PostgreSQL 16 (Docker) |
| Driver DB (local) | `pg8000` |
| Driver DB (Spark) | PostgreSQL JDBC 42.7 |
| Stockage distribué | HDFS (Hadoop 3.2) |
| Visualisation | `Streamlit` + `Plotly` |
| Conteneurisation | Docker Compose |

---

## Données collectées

| Source | Données | Volume |
|--------|---------|--------|
| football-data.org API | Classement, matchs, équipes, buteurs | ~370 lignes |
| transfermarkt.com (scraping) | Valeur marchande, effectif, âge moyen | 18 lignes |
