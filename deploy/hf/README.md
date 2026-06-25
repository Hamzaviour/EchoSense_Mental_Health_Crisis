---
title: Echo Sense AI
emoji: 🧠
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Echo Sense AI

AI-powered mental health crisis detection, triage, and counseling platform.

## Live demo

Open the Space URL to use the full Echo Sense web application (React frontend + Flask API on port **7860**).

## Stack

- **Frontend:** React, Vite, Tailwind
- **Backend:** Flask, JWT, SQLite (embedded)
- **Vector store:** ChromaDB (embedded persistent)
- **AI:** OpenRouter, Deepgram (configure via Space secrets)

## Space secrets

Add these in **Settings → Repository secrets** on Hugging Face:

| Secret | Description |
|--------|-------------|
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT signing key |
| `OPENROUTER_API_KEY` | OpenRouter API key for chat/AI features |
| `DEEPGRAM_API_KEY` | Optional — voice transcription |
| `API_NINJAS_API_KEY` | Optional — sentiment analysis |
| `HF_TOKEN` | Hugging Face token (embeddings fallback) |

## Demo accounts

Register a **patient** or **counselor** from the login page:

- **Patient:** Login → *Create patient account* → `/register`
- **Counselor:** Login → *Register as counselor* → `/register/counselor`

Pre-seeded admin (from container startup): `admin@echo.local` / `admin123`

## Local development

See the main project README for full local setup with PostgreSQL and ChromaDB.
