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

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "etl_topic")

