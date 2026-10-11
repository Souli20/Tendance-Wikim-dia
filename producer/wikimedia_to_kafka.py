import json
import requests
import sseclient
from kafka import KafkaProducer

URL = "https://stream.wikimedia.org/v2/stream/recentchange"
HEADERS = {"User-Agent": "TendanceWikimedia/1.0 (projet universitaire ISSEA; davysouli400@gmail.com)"}
TOPIC = "wiki-changes"
KAFKA_SERVER = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

import time


def ouvrir_flux():
    reponse = requests.get(URL, headers=HEADERS, stream=True, timeout=(10, 60))
    reponse.raise_for_status()
    return sseclient.SSEClient(reponse)

envoyes = 0
attente = 1
try:
    while True:
        try:
            print("Connexion au flux Wikimedia...")
            client = ouvrir_flux()
            attente = 1
            for evenement in client.events():
                if not evenement.data:
                    continue
                donnees = json.loads(evenement.data)
                producer.send(TOPIC, donnees)
                envoyes += 1
                if envoyes % 100 == 0:
                    print(envoyes, "événements envoyés", flush=True)
            print("Flux fermé par le serveur, reconnexion...")
        except Exception as erreur:
            print("Erreur :", repr(erreur), "- nouvelle tentative dans", attente, "s")
        time.sleep(attente)
        attente = min(attente * 2, 30)
except KeyboardInterrupt:
    print("Arrêt demandé")
finally:
    producer.flush()
    producer.close()
