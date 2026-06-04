"""Kafka event producer for Phase 2 streaming architecture."""
import json
import os

_producer = None

TOPICS = [
    "patient_messages",
    "sentiment_results",
    "risk_analysis",
    "triage_events",
    "counselor_notifications",
    "emergency_alerts",
]


def _get_producer():
    global _producer
    if _producer is None:
        try:
            from confluent_kafka import Producer

            servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            _producer = Producer({"bootstrap.servers": servers})
        except Exception:
            _producer = False
    return _producer if _producer is not False else None


def publish_event(topic: str, payload: dict, key: str = None):
    producer = _get_producer()
    if not producer or topic not in TOPICS:
        return False
    try:
        producer.produce(
            topic,
            key=key,
            value=json.dumps(payload, default=str).encode("utf-8"),
        )
        producer.flush(timeout=2)
        return True
    except Exception:
        return False
