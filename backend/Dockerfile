FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Create log directories
RUN mkdir -p /var/log/cron /var/log/gunicorn

CMD ["sh", "config/start_backend.sh"]
