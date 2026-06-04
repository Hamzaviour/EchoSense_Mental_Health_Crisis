# Echo Sense

AI-powered mental health crisis detection, triage, and counseling platform.

## Stack

- **Frontend:** React, Vite, Material UI, Tailwind, Recharts, Axios
- **Backend:** Flask (modular monolith), JWT, PostgreSQL
- **Vector DB:** ChromaDB
- **AI:** OpenRouter, Deepgram, API Ninjas, Hugging Face datasets

## Quick Start

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your API keys (never commit .env)
```

### 2. Docker (recommended)

```bash
cd docker
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:5000/api/health
- ChromaDB: http://localhost:8000

### 3. Local development

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python scripts/init_db.py
python run.py
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**RAG ingestion:**

```bash
cd backend
python scripts/ingest_mentalchat16k.py --limit 200 --model minilm
```

**Dataset exploration (console + HTML report):**

```bash
cd backend
python scripts/explore_mentalchat16k.py --limit 500 --samples 5 --open
```

Report is written to `backend/data/exploration/mentalchat16k_report.html`.

On **Python 3.14 / Windows**, local MiniLM (torch/onnxruntime) may fail to load native DLLs. The ingest script auto-falls back to the Hugging Face Inference API when `HF_TOKEN` is set, then to offline `--model simple` if needed. For best local embeddings, use **Python 3.11 or 3.12** in a venv with `pip install -r requirements.txt`.

### 4. Demo accounts

Register a patient at `/register`. Create a counselor:

```bash
curl -X POST http://localhost:5000/api/auth/register-counselor \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Dr. Smith","email":"counselor@echo.local","password":"counselor123"}'
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Patient registration |
| `POST /api/auth/login` | JWT login |
| `GET /api/chat/greeting` | Personalized greeting |
| `POST /api/chat/message` | Chat + RAG + risk |
| `POST /api/chat/voice` | Voice → Deepgram → chat |
| `GET /api/counselor/queue` | Patient queue by risk |
| `POST /api/counselor/copilot` | AI counselor suggestions |
| `GET /api/escalations/{id}/pdf` | Emergency PDF |

## Phase 2

See `docker/docker-compose.full.yml` for Kafka, Spark, Prometheus, Grafana, and Socket.IO.

## Disclaimer

Echo Sense is a decision-support tool. It does not replace licensed mental health professionals. Crisis: **Umang 0311-7786264**.
