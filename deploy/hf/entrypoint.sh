#!/bin/bash
set -euo pipefail

mkdir -p /home/user/data/chroma /home/user/data/reports
export DATABASE_URL="${DATABASE_URL:-sqlite:////home/user/data/echosense.db}"
export CHROMA_PERSIST_DIR="${CHROMA_PERSIST_DIR:-/home/user/data/chroma}"
export HF_SPACE=1
export SOCKETIO_ENABLED=false
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-simple}"

cd /app/backend
python scripts/init_db.py
python scripts/create_admin.py || true
exec gunicorn -b 0.0.0.0:7860 -w 1 --threads 4 --timeout 300 wsgi:app
