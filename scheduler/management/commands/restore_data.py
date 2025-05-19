"""
Management command to restore application data from backups.
"""
import os
import logging
import json
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from scheduler.models import Student, Course, Schedule, Section

logger = logging.getLogger('scheduler')

class Command(BaseCommand):
    help = 'Restore scheduler data from JSON backup files'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_dir',
            help='Directory containing the backup files to restore from'
        )
        parser.add_argument(
            '--timestamp',
            help='Specific timestamp to restore from (format: YYYYMMDD_HHMMSS)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before restoration'
        )

    def handle(self, *args, **options):
        backup_dir = options['backup_dir']
        timestamp = options['timestamp']
        clear_data = options['clear']
        
        if not os.path.exists(backup_dir):
            raise CommandError(f"Backup directory {backup_dir} does not exist")
            
        # Find all available backups if timestamp not provided
        if not timestamp:
            # Look for summary files to identify available backups
            summary_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_summary_')]
            
            if not summary_files:
                raise CommandError("No backup summaries found in the directory")
                
            # Sort by timestamp (newest first)
            summary_files.sort(reverse=True)
            
            # Use the most recent backup
            timestamp = summary_files[0].replace('backup_summary_', '').replace('.json', '')
            
            self.stdout.write(self.style.WARNING(
                f"No timestamp specified, using most recent: {timestamp}"
            ))
        
        # Map of model names to their classes
        models_map = {
            'students': Student,
            'courses': Course,
            'schedules': Schedule,
            'sections': Section,
        }
        
        # Start the restoration process inside a transaction
        try:
            with transaction.atomic():
                if clear_data:
                    self.stdout.write("Clearing existing data...")
                    # Delete in reverse dependency order
                    Section.objects.all().delete()
                    Schedule.objects.all().delete()
                    Student.objects.all().delete()
                    Course.objects.all().delete()
                
                # Restore each model from its backup file
                for name, model in models_map.items():
                    file_path = os.path.join(backup_dir, f"{name}_{timestamp}.json")
                    
                    if not os.path.exists(file_path):
                        self.stdout.write(self.style.WARNING(
                            f"Backup file for {name} not found: {file_path}"
                        ))
                        continue
                    
                    self.stdout.write(f"Restoring {name} from {file_path}...")
                    
                    with open(file_path, 'r') as f:
                        objects = serializers.deserialize('json', f)
                        object_count = 0
                        
                        for obj in objects:
                            obj.save()
                            object_count += 1
                            
                        self.stdout.write(self.style.SUCCESS(
                            f"Successfully restored {object_count} {name}"
                        ))
                        logger.info(f"Restored {object_count} {name} from {file_path}")
                
                self.stdout.write(self.style.SUCCESS(
                    f"Data restoration completed successfully from timestamp {timestamp}"
                ))
                
        except Exception as e:
            error_msg = f"Error restoring data: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise CommandError(error_msg)
