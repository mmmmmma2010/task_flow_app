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
# Create superuser if it doesn't exist (for any environment)

echo "Ensuring superuser exists..."
python manage.py shell <<'END'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin123')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser created: {username}/{password}")
else:
    print(f"Superuser '{username}' already exists")
END

echo "Entrypoint script completed!"

# Execute the main command
exec "$@"
