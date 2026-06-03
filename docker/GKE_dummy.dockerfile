FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    google-cloud-pubsub==2.31.1 \
    google-cloud-storage==3.10.1 \
    google-auth==2.49.2

COPY GKE_dummy.py .

CMD ["python", "GKE_dummy.py"]