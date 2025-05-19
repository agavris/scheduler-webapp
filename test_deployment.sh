#!/bin/bash
# Test script for verifying Course Scheduler deployment and functionality
# This script checks essential services and application functionality

echo "=== Course Scheduler Deployment Test ==="
echo "Testing started at $(date)"
echo

# Function to check service availability
check_service() {
  local service=$1
  local url=$2
  local expected_code=$3
  
  echo "Testing $service..."
  status_code=$(curl -s -o /dev/null -w "%{http_code}" $url)
  
  if [ "$status_code" = "$expected_code" ]; then
    echo "✅ $service is available (status code: $status_code)"
    return 0
  else
    echo "❌ $service is not available (status code: $status_code, expected: $expected_code)"
    return 1
  fi
}

# Check environment variables
echo "Checking environment variables..."
if [ -f .env ]; then
  echo "✅ .env file exists"
else
  echo "❌ .env file does not exist"
  exit 1
fi

# Check if Docker is running
echo "Checking if Docker is running..."
if docker info > /dev/null 2>&1; then
  echo "✅ Docker is running"
else
  echo "⚠️ Docker is not running. Attempting to start Docker..."
  
  # Check the OS and start Docker accordingly
  if [[ "$(uname -s)" == "Darwin" ]]; then
    # macOS - start Docker Desktop
    echo "Starting Docker Desktop for Mac..."
    open -a Docker
    
    # Wait for Docker to start (up to 30 seconds)
    echo "Waiting for Docker to start..."
    countdown=30
    while [ $countdown -gt 0 ]; do
      if docker info > /dev/null 2>&1; then
        echo "✅ Docker started successfully"
        break
      fi
      echo -n "."
      sleep 1
      countdown=$((countdown-1))
    done
    
    # Verify Docker is running
    if ! docker info > /dev/null 2>&1; then
      echo "\n❌ Failed to start Docker automatically. Please start Docker Desktop manually."
      exit 1
    fi
  else
    # Linux - try systemd service
    echo "Attempting to start Docker service..."
    sudo systemctl start docker || sudo service docker start
    
    # Wait for Docker to start
    echo "Waiting for Docker to start..."
    countdown=15
    while [ $countdown -gt 0 ]; do
      if docker info > /dev/null 2>&1; then
        echo "✅ Docker started successfully"
        break
      fi
      echo -n "."
      sleep 1
      countdown=$((countdown-1))
    done
    
    # Verify Docker is running
    if ! docker info > /dev/null 2>&1; then
      echo "\n❌ Failed to start Docker service. Please start Docker manually."
      exit 1
    fi
  fi
fi

# Build and start containers if not already running
echo "Checking containers..."
if [ "$(docker ps -q -f name=schedulerwebserver_web)" ]; then
  echo "✅ Application container is running"
else
  echo "⚠️ Application container is not running, starting containers..."
  docker-compose up -d
  sleep 10  # Give containers time to start
fi

# Test web application availability
base_url=${APP_URL:-"http://localhost:8080"}
check_service "Web Application" "$base_url" "200" || check_service "Web Application" "$base_url" "302"

# Test login page
check_service "Login Page" "$base_url/login/" "200"

# Test authentication API
check_service "API Endpoint" "$base_url/api/" "200" || check_service "API Endpoint" "$base_url/api/" "403"

echo
echo "=== Test Summary ==="
echo "Basic availability tests completed."
echo "To test administrator account creation:"
echo "1. Login to admin interface at $base_url/admin/ with superuser credentials"
echo "2. Navigate to 'Users' under 'Authentication and Authorization'"
echo "3. Click 'Add User' to create a new user account"
echo "4. After user creation, navigate to 'User preferences' under 'Scheduler'"
echo "5. Click 'Add User preference' and select the user you just created"
echo 
echo "Administrator can create users via the custom management command:"
echo "docker exec -it schedulerwebserver_web python manage.py create_user [username] [email]"
echo "  Options:"
echo "  --staff     : Make the user a staff member with admin access"
echo "  --superuser : Make the user a superuser with full privileges"
echo
echo "Testing completed at $(date)"
