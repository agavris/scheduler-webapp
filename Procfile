web: gunicorn scheduler_project.wsgi --log-file -
worker: celery -A scheduler_project worker -l info
