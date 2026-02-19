#!/bin/bash

# Entrypoint script for Docker container
# This script handles initialization tasks before starting the application

set -e

echo "Starting entrypoint script..."

# Wait for services using Python script
python docker/wait_for_services.py

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
