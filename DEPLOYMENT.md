# Course Scheduler Deployment Guide

## Overview

This document provides instructions for deploying the Course Scheduler application in a production environment. The application is designed to be deployed using Docker and Docker Compose, which simplifies the setup process and ensures consistency across different environments.

### Security Considerations

- Always use HTTPS in production
- Set strong passwords for database and admin user
- Keep your secret key secure and use environment variables
- Regularly update dependencies
- User authentication is required for all sensitive operations
- Consider IP whitelisting for added security in restricted environments

### Key Features

- **User Authentication**: Full login and registration system to secure access to scheduling features
- **User Preferences**: Customizable settings for each user including themes and scheduling parameters
- **Advanced Scheduling Options**: Multiple run optimization and priority weighting
- **Data Backup & Restore**: Built-in tools for backing up and restoring application data

## Authentication System

The application includes a complete authentication system with the following features:

- User registration with automatic creation of user preferences
- Secure login with Django's authentication system
- Password management and validation
- Session management and security
- Role-based access control for administrators

User access is required for all scheduler operations, including viewing courses, students, and schedules.

## Prerequisites

- Docker and Docker Compose installed on the host machine
- Domain name (optional but recommended for production)
- SSL certificate (recommended for production)

## Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd schedulerwebserver
   ```

2. Create a `.env` file based on the provided `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your production values:
   - Generate a secure Django secret key
   - Configure database credentials
   - Set up email settings
   - Configure Sentry DSN (if using Sentry for error tracking)
   - Set admin credentials

## Deployment Options

### 1. Docker Compose Deployment (Recommended)

This is the easiest way to deploy the application with all its dependencies:

1. Start the application using the simplified script:
   ```bash
   ./run-scheduler.sh start
   ```

   Or manually with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Monitor the startup process:
   ```bash
   docker-compose logs -f
   ```

3. Access the application at `http://localhost` or your configured domain.

### 2. Manual Deployment

If you prefer to deploy without Docker:

1. Set up a PostgreSQL database and Redis server.

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables or create a `.env` file.

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Install and configure Gunicorn, Nginx, and Supervisor.

## SSL Configuration

For production environments, enabling HTTPS is strongly recommended:

1. Obtain an SSL certificate (Let's Encrypt is a free option).

2. Update the Nginx configuration in `nginx/default.conf` to use SSL:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name yourdomain.com;

       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       
       # Rest of your configuration
       ...
   }
   ```

3. Mount the SSL certificates in the Docker Compose file.

## Scaling

The application can be scaled horizontally:

1. Scale web workers:
   ```bash
   docker-compose up -d --scale web=3
   ```

2. Configure a load balancer in front of the web containers.

## Backups

The application automatically creates daily database backups, stored in the `backups` volume.

To manually create a backup:
```bash
docker-compose exec web python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

To restore from a backup:
```bash
docker-compose exec web python manage.py loaddata backup_file.json
```

## Monitoring

The application integrates with several monitoring tools:

1. **Flower**: Access at `http://localhost:5555` to monitor Celery tasks.

2. **Prometheus metrics**: Configure Prometheus to scrape metrics from `/metrics`.

3. **Sentry**: Error tracking is sent to Sentry if configured.

## Updates and Maintenance

To update the application:

1. Pull the latest changes:
   ```bash
   git pull
   ```

2. Rebuild and restart containers:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Common Issues and Troubleshooting

### Database Connection Issues
- Check PostgreSQL credentials
- Verify network connectivity between containers

### Task Queue Issues
- Ensure Redis is running and accessible
- Check Flower dashboard for failed tasks

### Performance Issues
- Monitor system resources with the built-in monitoring tools
- Consider scaling the application horizontally
- Optimize database queries and add indexes as needed

## Production Checklist

Before going live:

- [ ] Set `DEBUG=False` in production settings
- [ ] Use strong, unique passwords
- [ ] Configure SSL/TLS
- [ ] Set up automated backups
- [ ] Configure email notifications
- [ ] Set up monitoring and alerting
- [ ] Test failover and recovery procedures
- [ ] Perform security assessment

## Support and Resources

For additional help and resources:
- Application Documentation: See the `docs` directory
- Community Forums: [link to forums]
- Issue Tracker: [link to issue tracker]
