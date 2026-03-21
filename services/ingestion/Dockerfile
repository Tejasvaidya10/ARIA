FROM python:3.12-slim

# PySpark needs Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-21-jre-headless curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/__init__.py services/__init__.py
COPY services/shared/ services/shared/
COPY services/ingestion/ services/ingestion/
COPY pyproject.toml .

RUN pip install --no-cache-dir -r services/ingestion/requirements.txt && \
    python -m spacy download en_core_web_sm

EXPOSE 8000

CMD ["uvicorn", "services.ingestion.app:app", "--host", "0.0.0.0", "--port", "8000"]
