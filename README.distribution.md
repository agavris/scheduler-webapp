# Scheduler Application - Portable Distribution

This package contains a pre-configured Scheduler application that can be easily installed and run on any machine with Docker installed.

## Prerequisites

- Docker (https://docs.docker.com/get-docker/)
- Docker Compose (Usually included with Docker Desktop)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

## Installation

1. Extract the distribution package to a location of your choice:

   ```
   unzip scheduler-app.zip
   cd scheduler-app
   ```

2. Make the application launcher executable:

   ```
   chmod +x scheduler-app.sh
   ```

3. Run the setup:

   ```
   ./scheduler-app.sh setup
   ```

   This will:
   - Create the necessary data directories
   - Set up the environment file
   - Load the pre-built Docker images

4. Start the application:

   ```
   ./scheduler-app.sh start
   ```

5. Access the application at: http://localhost:8080

## Using the Application

- The first time you access the application, you'll need to log in with the admin credentials:
  - Username: admin (or the value set in your .env file)
  - Password: adminpassword (or the value set in your .env file)

- Once logged in, you can:
  - Import student and course data
  - Run the scheduling algorithms
  - View and export schedules
  - Configure user preferences

## Managing the Application

The `scheduler-app.sh` script provides several commands:

- `./scheduler-app.sh start` - Start the application
- `./scheduler-app.sh stop` - Stop the application
- `./scheduler-app.sh restart` - Restart the application
- `./scheduler-app.sh logs` - View application logs
- `./scheduler-app.sh status` - Check application status

## Data Persistence

All data is stored in the `data` directory:
- `data/postgres` - Database files
- `data/logs` - Application logs
- `data/static` - Static web files

## Customization

You can customize the application by editing the `.env` file. Important settings include:

- `DJANGO_SUPERUSER_USERNAME` - Admin username
- `DJANGO_SUPERUSER_PASSWORD` - Admin password
- `APP_PORT` - The port to access the application (default: 8080)

## Troubleshooting

If you encounter issues:

1. Check the logs: `./scheduler-app.sh logs`
2. Ensure Docker is running: `docker info`
3. Verify port 8080 is not in use by another application
4. Restart the application: `./scheduler-app.sh restart`

For persistent issues, check that your machine meets the minimum requirements.

## Security Notes

- This application is pre-configured for ease of use, not maximum security
- For production use, change the admin password and secret key in the .env file
- Consider enabling HTTPS for internet-facing deployments
