#!/bin/bash
set -e

# Create Scheduler App Distribution Package
# This script packages the application into a portable distribution

echo "========================================"
echo "   Creating Scheduler App Distribution"
echo "========================================"

# Variables
DIST_NAME="scheduler-app"
DIST_DIR="dist"
VERSION=$(date +"%Y.%m.%d")

# Create distribution directory
echo "Creating distribution directory..."
mkdir -p ${DIST_DIR}/${DIST_NAME}

# Build Docker images
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Save Docker images
echo "Saving Docker images..."
mkdir -p ${DIST_DIR}/${DIST_NAME}/images
docker save scheduler-web:latest -o ${DIST_DIR}/${DIST_NAME}/images/scheduler-web.tar
docker save postgres:14 -o ${DIST_DIR}/${DIST_NAME}/images/postgres.tar

# Copy necessary files
echo "Copying application files..."
cp docker-compose.prod.yml ${DIST_DIR}/${DIST_NAME}/docker-compose.yml
cp scheduler-app.sh ${DIST_DIR}/${DIST_NAME}/
cp README.distribution.md ${DIST_DIR}/${DIST_NAME}/README.md
cp .env.example ${DIST_DIR}/${DIST_NAME}/

# Create empty data directories
echo "Creating data directories..."
mkdir -p ${DIST_DIR}/${DIST_NAME}/data/postgres
mkdir -p ${DIST_DIR}/${DIST_NAME}/data/logs
mkdir -p ${DIST_DIR}/${DIST_NAME}/data/static

# Set execute permissions
echo "Setting file permissions..."
chmod +x ${DIST_DIR}/${DIST_NAME}/scheduler-app.sh

# Create the zip archive
echo "Creating distribution archive..."
cd ${DIST_DIR}
zip -r ${DIST_NAME}-${VERSION}.zip ${DIST_NAME}
cd ..

echo "========================================"
echo " Distribution package created successfully!"
echo " Location: ${DIST_DIR}/${DIST_NAME}-${VERSION}.zip"
echo "========================================"
echo " To deploy on a new machine:"
echo " 1. Install Docker and Docker Compose"
echo " 2. Extract the zip archive"
echo " 3. Run: ./scheduler-app.sh"
echo "========================================"
