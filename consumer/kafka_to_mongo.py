import json
import os
from datetime import datetime, timezone

from kafka import KafkaConsumer
from pymongo import MongoClient

TOPIC = "wiki-changes"
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "wiki_db"
COLLECTION = "events_raw"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    group_id="mongo-writer",
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

collection = MongoClient(MONGO_URI)[DB_NAME][COLLECTION]


def construire_document(evenement):
    return {
        "_id": evenement["meta"]["id"],
        "rc_id": evenement.get("id"),
        "wiki": evenement.get("wiki"),
        "title": evenement.get("title"),
        "namespace": evenement.get("namespace"),
        "type": evenement.get("type"),
        "user": evenement.get("user"),
        "robot": evenement.get("bot", False),
        "timestamp": datetime.fromtimestamp(evenement["timestamp"], tz=timezone.utc),
    }


ecrits = 0
try:
    for message in consumer:
        document = construire_document(message.value)
        collection.replace_one({"_id": document["_id"]}, document, upsert=True)
        ecrits += 1
        if ecrits % 100 == 0:
            print(ecrits, "documents écrits dans MongoDB")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
