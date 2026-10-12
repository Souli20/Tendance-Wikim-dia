#!/usr/bin/env bash
# Arrête proprement le pipeline (MongoDB reste actif).
KAFKA="$HOME/kafka_2.13-4.3.1"

echo "Arrêt du dashboard"
pkill -f "streamlit run"
echo "Arrêt de Spark"
pkill -f "spark/streaming_job.py"
sleep 5
echo "Arrêt du producer"
pkill -f "producer/wikimedia_to_kafka.py"
sleep 2
echo "Arrêt de Kafka"
"$KAFKA/bin/kafka-server-stop.sh"
sleep 5

echo
echo "===== État ====="
jps | grep -E "Kafka|SparkSubmit" || echo "Aucun processus du pipeline en cours."
