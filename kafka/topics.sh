#!/bin/sh
# Create Kafka topics for Echo Sense (run inside kafka container)
KAFKA_BOOTSTRAP=${KAFKA_BOOTSTRAP:-kafka:9092}
for topic in patient_messages sentiment_results risk_analysis triage_events counselor_notifications emergency_alerts; do
  kafka-topics --create --if-not-exists --bootstrap-server $KAFKA_BOOTSTRAP \
    --topic $topic --partitions 3 --replication-factor 1
done
echo "Topics created."
