#!/bin/bash

# Start Celery worker in the background
celery -A config worker --loglevel=info --concurrency=2 &

# Start Celery beat in the background
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
