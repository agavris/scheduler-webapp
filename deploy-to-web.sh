#!/bin/bash
set -e

# Scheduler Web Deployment Script
# This script sets up and deploys the Scheduler application for web access

# Variables (modify these)
DOMAIN="example.com"  # Replace with your actual domain

echo "========================================"
echo "   Scheduler Web Deployment"
echo "========================================"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script should be run as root or with sudo."
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt-get update
    apt-get install -y docker-compose
fi

# Set up directory structure
echo "Creating necessary directories..."
mkdir -p data/logs data/static data/postgres
mkdir -p nginx/certbot/conf nginx/certbot/www

# Update Nginx configuration with domain name
echo "Configuring Nginx for domain: $DOMAIN"
sed -i "s/example.com/$DOMAIN/g" nginx/conf/app.conf

# Create env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "ERROR: .env.example file not found!"
        exit 1
    fi
    
    # Generate secure password and secret key
    RANDOM_PASSWORD=$(openssl rand -base64 12)
    RANDOM_SECRET=$(openssl rand -base64 32)
    
    # Update .env file with secure values
    sed -i "s/adminpassword/$RANDOM_PASSWORD/g" .env
    sed -i "s/django-insecure-t-\$8%17n6n\*-#=\$m\*tbaf2=@u5m-6prv1%0y_o&9(+&h#k_q(j/$RANDOM_SECRET/g" .env
    sed -i "s/ALLOWED_HOSTS=localhost,127.0.0.1/ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN/g" .env
    
    echo "Generated secure password. Please make note of it:"
    echo "Admin username: admin"
    echo "Admin password: $RANDOM_PASSWORD"
fi

# Initialize SSL certificates
echo "Setting up SSL certificates for $DOMAIN..."
docker-compose -f docker-compose.web.yml up -d nginx
docker-compose -f docker-compose.web.yml run --rm certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --agree-tos -m admin@$DOMAIN --no-eff-email
docker-compose -f docker-compose.web.yml restart nginx

# Start the full stack
echo "Starting the application..."
docker-compose -f docker-compose.web.yml up -d

echo "========================================"
echo "   Scheduler Application Deployed!"
echo "========================================"
echo "Access your application at: https://$DOMAIN"
echo "========================================"
