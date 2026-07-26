#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER"; do
    sleep 2
done

echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."

exec gunicorn grievance.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1