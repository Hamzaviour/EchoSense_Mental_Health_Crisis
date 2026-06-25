# EchoSense — Hugging Face Docker Space (port 7860)
# https://huggingface.co/docs/hub/spaces-sdks-docker

FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=""
RUN npm run build

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user deploy/hf/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user backend/ backend/
COPY --chown=user --from=frontend-build /frontend/dist backend/static/
COPY --chown=user deploy/hf/entrypoint.sh entrypoint.sh

RUN chmod +x entrypoint.sh

ENV PYTHONPATH=/app/backend
ENV HF_SPACE=1
ENV PORT=7860
ENV FRONTEND_URL=https://hamzavelous-echosense-ai.hf.space

EXPOSE 7860
CMD ["bash", "entrypoint.sh"]
