FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# System deps for psycopg (build) — kept minimal for Phase 0.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Dev default; compose overrides the command. Prod uses gunicorn.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
