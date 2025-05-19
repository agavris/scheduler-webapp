"""
Celery configuration for the scheduler project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler_project.settings')

app = Celery('scheduler_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'backup-database-daily': {
        'task': 'scheduler.tasks.database_backup_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        'options': {'expires': 3600}
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
