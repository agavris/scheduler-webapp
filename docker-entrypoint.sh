#!/bin/bash
set -e

# Wait for PostgreSQL to be available
if [ "$DATABASE_URL" ]; then
  echo "Waiting for PostgreSQL..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.5
  done
  echo "PostgreSQL is available"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Checking for superuser..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler_project.settings_prod')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

# Choose what to run based on the command
if [ "$1" = "celery" ]; then
  echo "Starting Celery worker..."
  celery -A scheduler_project worker -l INFO
elif [ "$1" = "beat" ]; then
  echo "Starting Celery beat..."
  celery -A scheduler_project beat -l INFO
elif [ "$1" = "flower" ]; then
  echo "Starting Flower..."
  celery -A scheduler_project flower --port=5555
else
  echo "Starting Gunicorn server..."
  # Use PORT environment variable provided by Heroku, or default to 8000
  PORT=${PORT:-8000}
  gunicorn scheduler_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
fi
