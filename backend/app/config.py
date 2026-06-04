import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://echosense:echosense@localhost:5432/echosense",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "mental_health_knowledge")
    CHROMA_PATIENT_MEMORY_COLLECTION = os.getenv(
        "CHROMA_PATIENT_MEMORY_COLLECTION", "patient_session_memory"
    )

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
    API_NINJAS_API_KEY = os.getenv("API_NINJAS_API_KEY", "")
    HF_TOKEN = os.getenv("HF_TOKEN", "")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    RISK_CLASSIFIER_ENABLED = os.getenv("RISK_CLASSIFIER_ENABLED", "true").lower() == "true"

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    RATELIMIT_DEFAULT = "200 per hour"
    RATELIMIT_STORAGE_URI = "memory://"
