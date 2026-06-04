# Echo Sense Architecture

## Phase 1 — Modular Monolith

Single Flask application with module blueprints:

- `auth` — JWT registration/login
- `patient` — profile and consent
- `chat` — messages, voice, RAG pipeline
- `assessment` — PHQ-9, GAD-7, WHO-5
- `counselor` — queue, co-pilot, triage
- `escalation` — critical alerts and PDF
- `admin` — analytics
- `risk` — risk history API

## Data Flow

Patient message → sentiment (API Ninjas) → hybrid risk ensemble → optional assessment trigger → Chroma RAG retrieval → OpenRouter response → DB persist.

Critical risk → escalation + counselor notifications + ReportLab PDF.

## Phase 2

Kafka event bus wraps existing service functions. PySpark consumes `patient_messages` for NLP batch scoring. Socket.IO pushes counselor alerts. Prometheus `/metrics` + Grafana dashboards.
