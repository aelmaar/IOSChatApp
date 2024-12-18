#!/bin/bash

# Wait for postgres
while ! nc -z postgres 5432; do
  sleep 0.1
done

# Wait for redis
while ! nc -z redis 6379; do
  sleep 0.1
done

echo "Starting Daphne..."
exec daphne chat_app.asgi:application \
    -b 0.0.0.0 \
    -p 8001 \
    --access-log /var/log/daphne/access.log \
    -v 2 \
    2>&1 | tee -a /var/log/daphne/daphne.log
