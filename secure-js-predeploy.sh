#!/bin/bash
# Pre-deployment script to secure JavaScript files
# Run this script before building your Docker image or deploying to web

echo "Securing JavaScript files for deployment..."

# Create directories if they don't exist
mkdir -p staticfiles

# Run collectstatic to gather all static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Obfuscate JavaScript files
echo "Obfuscating JavaScript files..."
python manage.py obfuscate_js

# Apply build process using the build-js script if available
if [ -f "./build-js.sh" ]; then
    echo "Running advanced JS build process..."
    ./build-js.sh
fi

echo "JavaScript security process complete!"
echo "Your JS files are now ready for secure deployment."
