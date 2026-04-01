import os
from dotenv import load_dotenv

load_dotenv()

# API
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"
API_RATE_LIMIT_DELAY = 6  # secondes entre chaque requête (plan gratuit = 10 req/min)

# Compétition cible
TARGET_COMPETITION = "FL1"  # Ligue 1

# PostgreSQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "football_dw"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Chemins Data Lake
DATA_LAKE_RAW_API = "data_lake/raw/api"
DATA_LAKE_RAW_SCRAPED = "data_lake/raw/scraped"
DATA_LAKE_PROCESSED = "data_lake/processed"
