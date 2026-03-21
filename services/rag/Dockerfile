FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/__init__.py services/__init__.py
COPY services/shared/ services/shared/
COPY services/rag/ services/rag/
COPY pyproject.toml .

RUN pip install --no-cache-dir -r services/rag/requirements.txt

# Pre-download the embedding model so containers start fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8002

CMD ["uvicorn", "services.rag.app:app", "--host", "0.0.0.0", "--port", "8002"]
