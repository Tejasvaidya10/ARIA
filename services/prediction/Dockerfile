FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/__init__.py services/__init__.py
COPY services/shared/ services/shared/
COPY services/prediction/ services/prediction/
COPY models/ models/
COPY pyproject.toml .

RUN pip install --no-cache-dir -r services/prediction/requirements.txt

EXPOSE 8001

CMD ["uvicorn", "services.prediction.app:app", "--host", "0.0.0.0", "--port", "8001"]
