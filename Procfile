web: gunicorn scheduler_project.wsgi:application --log-file - --access-logfile - --error-logfile - --log-level info --bind 0.0.0.0:$PORT
worker: celery -A scheduler_project worker -l info
