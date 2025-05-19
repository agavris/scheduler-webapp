"""
Asynchronous tasks for the scheduler application.
"""
from celery import shared_task
import logging
import time
from datetime import datetime
import os
import subprocess
import json
from django.conf import settings
from django.core import management
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Configure logger
logger = logging.getLogger('scheduler')

@shared_task(bind=True, max_retries=3)
def schedule_generation_task(self, data, user_email=None):
    """
    Generate a schedule asynchronously and send an email notification when complete.
    
    Args:
        data (dict): The input data for schedule generation
        user_email (str, optional): Email to notify when complete
    
    Returns:
        dict: The result of the schedule generation
    """
    from .ortools_scheduler import ORToolsScheduler
    
    start_time = time.time()
    logger.info(f"Starting schedule generation task at {datetime.now()}")
    
    try:
        # Generate the schedule
        scheduler = ORToolsScheduler()
        result = scheduler.generate_schedule(data)
        
        # Record execution time
        execution_time = time.time() - start_time
        result['execution_time'] = execution_time
        
        # Log completion
        logger.info(f"Schedule generation completed in {execution_time:.2f} seconds")
        
        # Send email notification if requested
        if user_email:
            send_schedule_notification(user_email, result)
            
        return result
    except Exception as exc:
        logger.error(f"Schedule generation failed: {str(exc)}")
        self.retry(exc=exc, countdown=60*5)  # Retry in 5 minutes
        raise

@shared_task
def database_backup_task():
    """Create a backup of the database."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
    
    try:
        # Use Django's dumpdata management command to create a JSON backup
        management.call_command('dumpdata', output=backup_file)
        logger.info(f"Database backup created at {backup_file}")
        
        # Remove old backups (keep only last 10)
        backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
        if len(backup_files) > 10:
            for old_file in backup_files[:-10]:
                os.remove(old_file)
                logger.info(f"Removed old backup: {old_file}")
                
        return {'status': 'success', 'backup_file': backup_file}
    except Exception as exc:
        logger.error(f"Database backup failed: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}

def send_schedule_notification(email, result):
    """
    Send an email notification that a schedule has been generated.
    
    Args:
        email (str): Email address to send the notification to
        result (dict): Results from the scheduling operation
    """
    subject = 'Schedule Generation Complete'
    
    context = {
        'timestamp': datetime.now(),
        'stats': {
            'perfect_count': result.get('perfect_count', 0),
            'partial_count': result.get('partial_count', 0),
            'unsatisfied_count': result.get('unsatisfied_count', 0)
        },
        'execution_time': f"{result.get('execution_time', 0):.2f}"
    }
    
    html_message = render_to_string('scheduler/email/schedule_complete.html', context)
    text_message = f"Your schedule has been generated. Perfect matches: {context['stats']['perfect_count']}, Partial matches: {context['stats']['partial_count']}, Unsatisfied: {context['stats']['unsatisfied_count']}. Time taken: {context['execution_time']} seconds."
    
    try:
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Schedule notification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
