# Plan d'implémentation — Pipeline Big Data Football

## Objectif
Pipeline complet : collecte → stockage brut → transformation → Data Warehouse → visualisation
Source principale : API football-data.org v4 + scraping web complémentaire
Compétitions visée : Ligue 1

---

## Architecture cible

```
projet/
├── ingestion/
│   ├── api_client.py          # Client API football-data.org
│   └── scraper.py             # Scraping web complémentaire
├── data_lake/
│   ├── raw/
│   │   ├── api/               # JSON bruts de l'API
│   │   └── scraped/           # CSV/HTML bruts du scraping
│   └── processed/             # Données transformées
├── transformation/
│   ├── transform_api.py       # Nettoyage et normalisation des données API
│   ├── transform_scraped.py   # Nettoyage des données scrapées
│   └── merge.py               # Fusion des deux sources
├── warehouse/
│   ├── schema.sql             # Schéma PostgreSQL
│   └── load.py                # Chargement dans PostgreSQL
├── dashboard/
│   └── app.py                 # Application Streamlit
├── config/
│   └── config.py              # Configuration (clés API, connexion DB)
├── requirements.txt
└── README.md
```

---

## Phase 1 — Ingestion API (football-data.org v4)

### Données à collecter
- **Compétitions** : liste des ligues disponibles (`/v4/competitions`)
- **Classements** : table de classement d'une ligue (`/v4/competitions/{code}/standings`)
- **Matchs** : résultats et fixtures (`/v4/competitions/{code}/matches`)
- **Équipes** : infos équipes d'une compétition (`/v4/competitions/{code}/teams`)
- **Buteurs** : top scorers (`/v4/competitions/{code}/scorers`)

### Tâches
- [ ] Créer `config/config.py` avec la clé API et les paramètres
- [ ] Créer `ingestion/api_client.py` :
  - Classe `FootballAPIClient` avec gestion du rate-limiting (10 req/min sur plan gratuit)
  - Méthodes : `get_competitions()`, `get_standings()`, `get_matches()`, `get_teams()`, `get_scorers()`
  - Sauvegarde automatique des réponses JSON dans `data_lake/raw/api/`
  - Gestion des erreurs HTTP et retry
- [ ] Tester la collecte sur au moins 2 compétitions (ex: PL, PD)

---

## Phase 2 — Scraping web

### Source à scraper
- **Objectif** : enrichir les données avec des infos non disponibles via l'API gratuite
- **Cible suggérée** : `fbref.com` ou `transfermarkt.com` — statistiques avancées des joueurs/équipes (xG, possession, passes, etc.)
- **Outil** : BeautifulSoup (si pages statiques) ou Selenium (si JavaScript)

### Tâches
- [ ] Identifier les pages cibles et la structure HTML
- [ ] Créer `ingestion/scraper.py` :
  - Fonction `scrape_team_stats(league_name)` → scraping des stats d'équipes
  - Sauvegarde en CSV dans `data_lake/raw/scraped/`
  - Respect du `robots.txt` et délais entre requêtes (`time.sleep`)
- [ ] Gérer les cas d'erreur (timeout, structure HTML changeante)

---

## Phase 3 — Data Lake local

### Structure de fichiers
```
data_lake/
├── raw/
│   ├── api/
│   │   ├── competitions_YYYYMMDD.json
│   │   ├── standings_PL_YYYYMMDD.json
│   │   ├── matches_PL_YYYYMMDD.json
│   │   ├── teams_PL_YYYYMMDD.json
│   │   └── scorers_PL_YYYYMMDD.json
│   └── scraped/
│       └── team_stats_PL_YYYYMMDD.csv
└── processed/
    ├── standings_clean.csv
    ├── matches_clean.csv
    ├── teams_clean.csv
    ├── scorers_clean.csv
    └── merged_teams.csv
```

### Tâches
- [ ] Créer les dossiers `data_lake/raw/api/`, `data_lake/raw/scraped/`, `data_lake/processed/`
- [ ] Vérifier que chaque script d'ingestion sauvegarde bien les fichiers horodatés

---

## Phase 4 — Transformation (pandas)

### Tâches
- [ ] Créer `transformation/transform_api.py` :
  - Normaliser les JSON imbriqués en DataFrames plats
  - Renommer les colonnes en snake_case
  - Typer correctement les colonnes (dates → datetime, scores → int, etc.)
  - Dédupliquer
  - Exporter en CSV dans `data_lake/processed/`
- [ ] Créer `transformation/transform_scraped.py` :
  - Nettoyer le CSV scrapé (espaces, caractères spéciaux, valeurs manquantes)
  - Normaliser les noms d'équipes pour pouvoir faire la jointure
- [ ] Créer `transformation/merge.py` :
  - Fusionner les données API et scrapées sur la clé `team_name`
  - Exporter `merged_teams.csv`

---

## Phase 5 — Data Warehouse PostgreSQL

### Schéma de base de données
Tables cibles :
- `competitions(id, name, code, area, type)`
- `teams(id, name, short_name, tla, area, founded, venue)`
- `standings(id, competition_id, season, team_id, position, played, won, draw, lost, goals_for, goals_against, goal_diff, points)`
- `matches(id, competition_id, season, matchday, utc_date, status, home_team_id, away_team_id, home_score, away_score)`
- `scorers(id, competition_id, season, player_name, team_id, goals, assists, penalties)`
- `team_stats_scraped(id, team_id, xg, xg_against, possession_pct, passes_completed, source_url)` *(données scrapées)*

### Tâches
- [ ] Créer `warehouse/schema.sql` avec les CREATE TABLE et contraintes FK
- [ ] Créer `warehouse/load.py` :
  - Connexion PostgreSQL via `psycopg2`
  - Lecture des CSV depuis `data_lake/processed/`
  - Insertion avec gestion des conflits (`ON CONFLICT DO UPDATE`)
  - Logs de chargement (nombre de lignes insérées/mises à jour)
- [ ] Créer la base `football_dw` dans PostgreSQL
- [ ] Appliquer le schéma et tester le chargement

---

## Phase 6 — Dashboard Streamlit

### Contenu du dashboard
- **Page 1 — Vue d'ensemble** : sélecteur de compétition, classement actuel, KPIs (meilleur buteur, meilleure attaque, meilleure défense)
- **Page 2 — Matchs** : calendrier/résultats filtrables par journée, visualisation des scores
- **Page 3 — Équipes** : comparaison de deux équipes (stats API + stats scrapées), radar chart
- **Page 4 — Joueurs** : top scorers, classement des buteurs avec filtres

### Visualisations
- Tableau de classement interactif (st.dataframe)
- Barres horizontales pour les buts marqués/encaissés
- Radar chart pour la comparaison d'équipes (matplotlib/plotly)
- Graphique d'évolution de classement sur les journées (si données disponibles)

### Tâches
- [ ] Créer `dashboard/app.py` avec navigation multi-pages (`st.sidebar`)
- [ ] Connexion directe à PostgreSQL depuis Streamlit
- [ ] Implémenter les 4 pages avec leurs visualisations
- [ ] Tester le dashboard avec les données réelles

---

## Phase 7 — Finalisation

- [ ] Créer `requirements.txt` avec toutes les dépendances
- [ ] Créer `README.md` avec les instructions d'installation et d'exécution
- [ ] Script `main.py` orchestrant le pipeline complet (ingestion → transform → load)
- [ ] Préparer les slides de soutenance (résumé de l'architecture, démo, difficultés rencontrées)

---

## Dépendances Python

```
requests
beautifulsoup4
selenium
pandas
psycopg2-binary
streamlit
plotly
python-dotenv
```

---

## Notes importantes

- **Clé API football-data.org** : plan gratuit = 10 requêtes/minute, accès aux 12 compétitions principales
- **Rate limiting** : implémenter un délai de 6 secondes entre chaque appel API
- **Clé API** : stocker dans un fichier `.env` (ne jamais committer)
- **PostgreSQL** : installation locale requise, créer la DB `football_dw` avant le chargement

---

## Ordre d'exécution recommandé

1. `ingestion/api_client.py` → collecte et sauvegarde dans le Data Lake
2. `ingestion/scraper.py` → scraping et sauvegarde dans le Data Lake
3. `transformation/transform_api.py` → nettoyage des données API
4. `transformation/transform_scraped.py` → nettoyage des données scrapées
5. `transformation/merge.py` → fusion
6. `warehouse/load.py` → chargement en base
7. `dashboard/app.py` → lancement du dashboard
