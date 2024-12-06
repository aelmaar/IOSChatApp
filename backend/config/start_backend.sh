#!/bin/bash

# Wait until PostgreSQL is ready
until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

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
