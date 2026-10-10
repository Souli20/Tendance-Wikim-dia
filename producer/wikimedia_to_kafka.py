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
print("Connexion au flux Wikimedia...")
reponse = requests.get(URL, headers=HEADERS, stream=True)
client = sseclient.SSEClient(reponse)

envoyes = 0
try:
    for evenement in client.events():
        if not evenement.data:
            continue
        donnees = json.loads(evenement.data)
        producer.send(TOPIC, donnees)
        envoyes += 1
        if envoyes % 100 == 0:
            print(envoyes, "événements envoyés")
except KeyboardInterrupt:
    print("Arrêt demandé")
finally:
    producer.flush()
    producer.close()
