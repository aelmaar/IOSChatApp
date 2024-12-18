#!/bin/bash

# Wait for postgres
while ! nc -z postgres 5432; do
  sleep 0.1
done

# Wait for redis
while ! nc -z redis 6379; do
  sleep 0.1
done

# Create log directory for Gunicorn
mkdir -p /var/log/gunicorn

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Set up cron environment
printenv >> /etc/environment

echo "Setting up cron jobs..."
python manage.py crontab add

# Start cron service
service cron start

echo "Starting Gunicorn..."
exec gunicorn chat_app.wsgi:application \
    --config config/gunicorn.conf.py
