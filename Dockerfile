# Slim Python base; the SaaS backend needs no browser (the "buy" step runs in
# the user's own browser via deep links, not on our servers).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

EXPOSE 8000

# Uvicorn serves the FastAPI app; scale replicas horizontally in k8s.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
