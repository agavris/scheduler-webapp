"""
Management command to backup application data.
"""
import os
import logging
import json
from datetime import datetime
from django.core import serializers
from django.core.management.base import BaseCommand
from django.conf import settings
from scheduler.models import Student, Course, Schedule, Section

logger = logging.getLogger('scheduler')

class Command(BaseCommand):
    help = 'Backup scheduler data to JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            dest='output_dir',
            default=os.path.join(settings.BASE_DIR, 'backups'),
            help='Directory to store backup files'
        )

    def handle(self, *args, **options):
        # Create timestamp for the backup files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = options['output_dir']
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.stdout.write(self.style.SUCCESS(f"Starting backup at {timestamp}..."))
        
        # Backup each model
        models_to_backup = {
            'students': Student,
            'courses': Course,
            'schedules': Schedule,
            'sections': Section,
        }
        
        backup_results = {}
        
        for name, model in models_to_backup.items():
            try:
                file_path = os.path.join(output_dir, f"{name}_{timestamp}.json")
                
                # Query all objects from the model
                queryset = model.objects.all()
                count = queryset.count()
                
                # Serialize the data to JSON
                with open(file_path, 'w') as f:
                    serializers.serialize('json', queryset, indent=4, stream=f)
                
                backup_results[name] = {
                    'status': 'success',
                    'count': count,
                    'file': file_path
                }
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully backed up {count} {name} to {file_path}"
                ))
                logger.info(f"Backed up {count} {name} to {file_path}")
                
            except Exception as e:
                error_msg = f"Error backing up {name}: {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(error_msg)
                backup_results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Create a summary file
        summary_path = os.path.join(output_dir, f"backup_summary_{timestamp}.json")
        with open(summary_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results': backup_results
            }, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS(
            f"Backup completed. Summary saved to {summary_path}"
        ))
