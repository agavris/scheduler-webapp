# Deploying to Digital Ocean

This document provides step-by-step instructions for deploying the scheduler web application to Digital Ocean.

## Prerequisites

- Digital Ocean account
- Docker and Docker Compose installed on your local machine
- doctl (Digital Ocean CLI) installed and configured

## Deployment Steps

### 1. Create a Digital Ocean Droplet

1. Log in to your Digital Ocean account
2. Create a new Droplet with the following specifications:
   - Ubuntu 22.04 or newer
   - At least 2GB RAM (Recommended: 4GB for production)
   - At least 25GB SSD disk
   - Enable backups
   - Choose a datacenter region close to your users
   - Add your SSH key

### 2. Set Up Domain and DNS

1. Register your domain or use an existing one
2. Add your domain to Digital Ocean
3. Create A records pointing to your Droplet's IP address:
   - `@` (root domain)
   - `www` (subdomain)

### 3. Prepare the Server

SSH into your droplet:

```bash
ssh root@your-droplet-ip
```

Update the system and install Docker and Docker Compose:

```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose git
```

### 4. Set Up SSL Certificates

Install Certbot:

```bash
apt install -y certbot
```

Obtain SSL certificates:

```bash
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Create a directory for SSL certificates:

```bash
mkdir -p /path/to/app/nginx/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/app/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/app/nginx/ssl/
```

### 5. Clone and Configure the Application

Clone the repository:

```bash
git clone https://github.com/yourusername/scheduler-webapp.git /path/to/app
cd /path/to/app
```

Create the required directories:

```bash
mkdir -p data/postgres data/redis data/logs/nginx data/static data/media
```

### 6. Configure Environment Variables

Create a production .env file:

```bash
cp .env.example .env.production
```

Edit the .env.production file and set the following variables:

```
DJANGO_SECRET_KEY=your_very_secure_random_secret_key
POSTGRES_PASSWORD=your_secure_database_password
REDIS_PASSWORD=your_secure_redis_password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_secure_admin_password
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SERVER_NAME=yourdomain.com
ENABLE_SSL=True
DB_USE_SSL=True
```

### 7. Deploy the Application

Link the production env file:

```bash
ln -sf .env.production .env
```

Start the application:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 8. Set Up Database Backups

Create a backup script:

```bash
cat > /path/to/app/backup-db.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/path/to/app/backups"
mkdir -p $BACKUP_DIR

# Get environment variables
source /path/to/app/.env

# Backup PostgreSQL database
docker exec -t $(docker ps -qf "name=db") pg_dump -U postgres scheduler > $BACKUP_DIR/scheduler_$TIMESTAMP.sql

# Compress the backup
gzip $BACKUP_DIR/scheduler_$TIMESTAMP.sql

# Remove backups older than 7 days
find $BACKUP_DIR -name "scheduler_*.sql.gz" -type f -mtime +7 -delete
EOF

chmod +x /path/to/app/backup-db.sh
```

Set up a daily cron job for backups:

```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/app/backup-db.sh") | crontab -
```

## Environment Variables Checklist

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| DJANGO_SECRET_KEY | Django secret key | Yes | `your_very_secure_random_secret_key` |
| POSTGRES_PASSWORD | PostgreSQL password | Yes | `your_secure_database_password` |
| REDIS_PASSWORD | Redis password | Yes | `your_secure_redis_password` |
| DJANGO_SUPERUSER_USERNAME | Django admin username | Yes | `admin` |
| DJANGO_SUPERUSER_PASSWORD | Django admin password | Yes | `your_secure_admin_password` |
| DJANGO_SUPERUSER_EMAIL | Django admin email | Yes | `admin@yourdomain.com` |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts | Yes | `yourdomain.com,www.yourdomain.com` |
| CSRF_TRUSTED_ORIGINS | Comma-separated list of trusted origins | Yes | `https://yourdomain.com,https://www.yourdomain.com` |
| SERVER_NAME | Server name | Yes | `yourdomain.com` |
| ENABLE_SSL | Enable SSL | Yes | `True` |
| DB_USE_SSL | Use SSL for database | Yes | `True` |
| WEB_MEMORY | Memory limit for web container | No | `512M` |
| DB_MEMORY | Memory limit for database container | No | `512M` |
| REDIS_MEMORY | Memory limit for Redis container | No | `256M` |
| NGINX_MEMORY | Memory limit for Nginx container | No | `128M` |
| APP_PORT | HTTP port | No | `80` |
| HTTPS_PORT | HTTPS port | No | `443` |
| EMAIL_HOST | SMTP host | No | `smtp.gmail.com` |
| EMAIL_PORT | SMTP port | No | `587` |
| EMAIL_USER | SMTP username | No | `your-email@gmail.com` |
| EMAIL_PASSWORD | SMTP password | No | `your-email-password` |
| DEFAULT_FROM_EMAIL | Default sender email | No | `noreply@yourdomain.com` |

## Maintenance

### Updating the Application

```bash
cd /path/to/app
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoring

Set up monitoring with Digital Ocean Monitoring or install Prometheus and Grafana for more detailed monitoring.

## Troubleshooting

### Checking Logs

```bash
# View all container logs
docker-compose -f docker-compose.prod.yml logs

# View logs for a specific service
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs nginx
```

### Common Issues

1. **SSL Certificate Issues**: Ensure certificates are correctly placed in the nginx/ssl directory.
2. **Database Connection Issues**: Check PostgreSQL logs and ensure the password is correctly set.
3. **Static Files Not Loading**: Verify STATIC_ROOT and MEDIA_ROOT paths in Django settings.
