import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaProducer
from config.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def creer_producer():
    """Crée et retourne un KafkaProducer qui sérialise les valeurs en JSON."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )


def envoyer_messages(producer, type_donnee, records):
    """
    Envoie une liste de dicts vers Kafka.

    Args:
        producer: instance KafkaProducer
        type_donnee: identifiant du type ('competition', 'teams', etc.)
        records: liste de dicts représentant les lignes à envoyer
    """
    for record in records:
        message = {"type": type_donnee, "data": record}
        producer.send(KAFKA_TOPIC, value=message)
    producer.flush()
    print(f"  → {len(records)} message(s) '{type_donnee}' envoyé(s) vers Kafka")
