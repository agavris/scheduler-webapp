from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from scheduler.models import UserPreference
import getpass
import sys

class Command(BaseCommand):
    help = 'Creates a new user account with associated UserPreference'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new account')
        parser.add_argument('email', type=str, help='Email address for the new account')
        parser.add_argument('--staff', action='store_true', help='Make user a staff member with admin access')
        parser.add_argument('--superuser', action='store_true', help='Make user a superuser with full access')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        is_staff = options['staff']
        is_superuser = options['superuser']

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username "{username}" already exists'))
            return

        # Get password securely without echoing to console
        while True:
            password = getpass.getpass('Enter password: ')
            password_confirm = getpass.getpass('Confirm password: ')
            
            if password == password_confirm:
                break
            else:
                self.stdout.write(self.style.ERROR('Passwords do not match. Please try again.'))

        try:
            # Create user based on permissions level
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_staff=is_staff
                )
                if is_staff:
                    self.stdout.write(self.style.SUCCESS(f'Staff user "{username}" created successfully'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Regular user "{username}" created successfully'))
            
            # Create user preferences
            UserPreference.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f'User preferences created for {username}'))
            
            self.stdout.write(self.style.SUCCESS('Account setup complete'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {str(e)}'))
