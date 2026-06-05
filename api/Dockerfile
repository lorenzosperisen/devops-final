# --- Étage 1 : Builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

COPY requirements.txt .
# Installation des dépendances dans un dossier local isolé
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Étage 2 : Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Récupération uniquement des packages compilés de l'étage builder
COPY --from=builder /root/.local /root/.local
COPY api/ /app/api/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]