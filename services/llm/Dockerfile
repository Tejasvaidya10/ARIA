FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/__init__.py services/__init__.py
COPY services/shared/ services/shared/
COPY services/llm/ services/llm/
COPY pyproject.toml .

RUN pip install --no-cache-dir -r services/llm/requirements.txt

EXPOSE 8003

CMD ["uvicorn", "services.llm.app:app", "--host", "0.0.0.0", "--port", "8003"]
