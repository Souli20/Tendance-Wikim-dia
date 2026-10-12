#!/usr/bin/env bash
# Démarre tout le pipeline Wikimedia : MongoDB, Kafka, producer, Spark, dashboard.
set -u

PROJET="$HOME/Projet_Big_Data"
KAFKA="$HOME/kafka_2.13-4.3.1"
SPARK="/opt/spark"
PACKAGE="org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.4"
TOPIC="wiki-changes"

cd "$PROJET" || { echo "Dossier du projet introuvable"; exit 1; }
mkdir -p logs kafka-data
source venv/bin/activate

attendre_port() {
    local port="$1" nom="$2"
    for i in $(seq 1 60); do
        if ss -ltn | grep -q ":$port "; then
            echo "   OK : $nom est prêt"
            return 0
        fi
        sleep 2
    done
    echo "   ÉCHEC : $nom ne répond pas (voir logs/)"
    return 1
}

echo "[1/6] MongoDB"
if ! systemctl is-active --quiet mongod; then
    sudo systemctl start mongod
fi
attendre_port 27017 "MongoDB" || exit 1

echo "[2/6] Kafka"
if [ ! -f "$PROJET/kafka-data/meta.properties" ]; then
    echo "   Stockage Kafka non initialisé : formatage"
    ID="$("$KAFKA/bin/kafka-storage.sh" random-uuid)"
    "$KAFKA/bin/kafka-storage.sh" format --standalone -t "$ID" -c "$KAFKA/config/server.properties"
fi
if pgrep -f "kafka.Kafka" > /dev/null; then
    echo "   Kafka tourne déjà"
else
    nohup "$KAFKA/bin/kafka-server-start.sh" "$KAFKA/config/server.properties" > logs/kafka.log 2>&1 &
fi
attendre_port 9092 "Kafka" || exit 1

echo "[3/6] Topic $TOPIC"
"$KAFKA/bin/kafka-topics.sh" --create --if-not-exists --topic "$TOPIC" \
    --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo "[4/6] Producer (Wikimedia -> Kafka)"
if pgrep -f "producer/wikimedia_to_kafka.py" > /dev/null; then
    echo "   Le producer tourne déjà"
else
    nohup python -u producer/wikimedia_to_kafka.py > logs/producer.log 2>&1 &
    echo "   Lancé"
fi

echo "[5/6] Spark Streaming"
if pgrep -f "spark/streaming_job.py" > /dev/null; then
    echo "   Spark tourne déjà"
else
    nohup env PYSPARK_PYTHON="$PROJET/venv/bin/python" "$SPARK/bin/spark-submit" \
        --packages "$PACKAGE" spark/streaming_job.py > logs/spark.log 2>&1 &
    echo "   Lancé (le démarrage prend 1 à 2 minutes)"
fi

echo "[6/6] Dashboard Streamlit"
if pgrep -f "streamlit run" > /dev/null; then
    echo "   Le dashboard tourne déjà"
else
    nohup streamlit run dashboard/app.py > logs/dashboard.log 2>&1 &
    echo "   Lancé"
fi
attendre_port 8501 "Dashboard" || true

echo
echo "===== État ====="
jps | grep -E "Kafka|SparkSubmit"
pgrep -af "producer/wikimedia_to_kafka.py" | head -n 1
pgrep -af "streamlit run" | head -n 1
echo
echo "Dashboard : http://localhost:8501"
echo "Les premiers résultats arrivent après 2 à 3 minutes, et les blocs de tendance après environ 15 minutes de données."
