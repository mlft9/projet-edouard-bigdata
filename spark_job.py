"""
Spark batch job — lit les messages depuis Kafka et charge PostgreSQL.

Lancement (depuis le terminal) :
    docker exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.3 \
        /opt/spark-apps/spark_job.py
"""

import subprocess
import sys

# Installe psycopg2 dans /tmp (accessible en écriture par tous les utilisateurs)
_deps = "/tmp/pydeps"
subprocess.run(["pip", "install", f"--target={_deps}", "psycopg2-binary", "-q"], check=True)
sys.path.insert(0, _deps)

import json
import psycopg2
from pyspark.sql.functions import col, to_timestamp
from pyspark.sql import SparkSession

# ── Configuration ─────────────────────────────────────────────────────────────

KAFKA_BOOTSTRAP = "kafka:29092"       # adresse interne Docker
KAFKA_TOPIC     = "etl_topic"

HDFS_ROOT = "hdfs://namenode:8020"    # data lake HDFS

DB_HOST     = "postgres"
DB_PORT     = 5432
DB_NAME     = "football_dw"
DB_USER     = "postgres"
DB_PASSWORD = "postgres"

JDBC_URL   = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
JDBC_PROPS = {
    "user":     DB_USER,
    "password": DB_PASSWORD,
    "driver":   "org.postgresql.Driver",
}

# ── Initialisation Spark ──────────────────────────────────────────────────────

spark = SparkSession.builder \
    .appName("FootballETL") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ── Lecture batch depuis Kafka ────────────────────────────────────────────────

print("\n=== Lecture depuis Kafka ===")
raw_df = (
    spark.read
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

messages_df = raw_df.selectExpr("CAST(value AS STRING) AS json_str")
rows = messages_df.collect()
print(f"  → {len(rows)} message(s) reçus")

# ── Tri des messages par type ─────────────────────────────────────────────────

buckets = {
    "competition":   [],
    "teams":         [],
    "standings":     [],
    "matches":       [],
    "scorers":       [],
    "market_values": [],
}

for row in rows:
    msg = json.loads(row["json_str"])
    t = msg.get("type")
    if t in buckets:
        buckets[t].append(msg["data"])

for t, records in buckets.items():
    print(f"  {t}: {len(records)} enregistrement(s)")

# ── Sauvegarde dans HDFS (data lake raw) ─────────────────────────────────────

print("\n=== Sauvegarde dans HDFS ===")
try:
    for type_donnee, data in buckets.items():
        if data:
            df_hdfs = spark.createDataFrame(data)
            path = f"{HDFS_ROOT}/data/raw/{type_donnee}"
            df_hdfs.write.mode("overwrite").json(path)
            print(f"  → /data/raw/{type_donnee} ({len(data)} entrées)")
except Exception as e:
    print(f"  ⚠ HDFS indisponible, on continue sans : {e}")

# ── Truncation Postgres (ordre FK-safe) ───────────────────────────────────────

print("\n=== Truncation des tables ===")
conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT,
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
    TRUNCATE TABLE team_stats_scraped, scorers, standings, matches, teams, competitions
    RESTART IDENTITY CASCADE
""")
cur.close()
conn.close()
print("  → Tables tronquées")

# ── Écriture JDBC dans l'ordre FK ─────────────────────────────────────────────

print("\n=== Chargement en base ===")


def ecrire_table(data, table_name, drop_cols=None, cast_int=None, cast_ts=None):
    if not data:
        print(f"  (pas de données pour {table_name})")
        return
    df = spark.createDataFrame(data)
    if drop_cols:
        df = df.drop(*drop_cols)
    if cast_int:
        for c in cast_int:
            df = df.withColumn(c, col(c).cast("integer"))
    if cast_ts:
        for c in cast_ts:
            df = df.withColumn(c, to_timestamp(col(c)))
    df.write.jdbc(url=JDBC_URL, table=table_name, mode="append", properties=JDBC_PROPS)
    print(f"  → {len(data)} ligne(s) écrite(s) dans '{table_name}'")


# Parents d'abord, enfants ensuite (respecte les FK)
ecrire_table(buckets["competition"],   "competitions")
ecrire_table(buckets["teams"],         "teams")
# team_name absent de la table SQL standings
ecrire_table(buckets["standings"],     "standings",  drop_cols=["team_name"])
# utc_date = string → timestamp ; scores = float → integer
ecrire_table(buckets["matches"],       "matches",    cast_ts=["utc_date"], cast_int=["home_score", "away_score"])
# goals/assists/penalties peuvent être NaN (null API) → cast integer (NaN → null)
ecrire_table(buckets["scorers"],       "scorers",          cast_int=["goals", "assists", "penalties"])
# squad_size/foreigners → integer ; avg_age/market_value_m → float déjà OK
ecrire_table(buckets["market_values"], "team_stats_scraped", cast_int=["squad_size", "foreigners"])

spark.stop()
print("\n=== Spark job terminé ===")
