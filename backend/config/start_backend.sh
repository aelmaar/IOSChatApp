#!/bin/bash

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn chat_app.wsgi:application \
    --config config/gunicorn.conf.py
