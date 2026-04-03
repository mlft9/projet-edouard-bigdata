import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaProducer
from config.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def creer_producer():
    """Crée et retourne un KafkaProducer qui sérialise les valeurs en JSON."""
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
    except Exception as e:
        print(f"Erreur connexion Kafka ({KAFKA_BOOTSTRAP_SERVERS}) : {e}")
        raise


def envoyer_messages(producer, type_donnee, records):
    """
    Envoie une liste de dicts vers Kafka.

    Args:
        producer: instance KafkaProducer
        type_donnee: identifiant du type ('competition', 'teams', etc.)
        records: liste de dicts représentant les lignes à envoyer
    """
    try:
        for record in records:
            message = {"type": type_donnee, "data": record}
            producer.send(KAFKA_TOPIC, value=message)
        producer.flush()
        print(f"  → {len(records)} message(s) '{type_donnee}' envoyé(s) vers Kafka")
    except Exception as e:
        print(f"Erreur envoi Kafka (type='{type_donnee}') : {e}")
        raise
