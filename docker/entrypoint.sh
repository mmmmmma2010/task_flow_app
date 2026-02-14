#!/bin/bash

# Entrypoint script for Docker container
# This script handles initialization tasks before starting the application

set -e

echo "Starting entrypoint script..."

# Set default values for DB_HOST and DB_PORT if not set
export DB_HOST=${DB_HOST:-db}
export DB_PORT=${DB_PORT:-5432}

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (skip if already done in Dockerfile)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (for development)
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ]; then
    echo "Creating superuser (if not exists)..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
END
fi

echo "Entrypoint script completed!"

# Execute the main command
exec "$@"
