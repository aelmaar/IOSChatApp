FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y \
    postgresql-client \
    cron \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/cron

COPY . .
