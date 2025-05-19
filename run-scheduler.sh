#!/bin/bash

# Scheduler Web Server Control Script
# Supports both development and production modes

# Configuration
DEV_COMPOSE_FILE="docker-compose-dev.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"
DEFAULT_MODE="dev"

# Parse environment mode from arguments
MODE=${DEFAULT_MODE}
if [[ "$1" == "--prod" || "$1" == "--production" ]]; then
    MODE="prod"
    shift
elif [[ "$1" == "--dev" || "$1" == "--development" ]]; then
    MODE="dev"
    shift
fi

# Set the compose file based on mode
if [[ "${MODE}" == "prod" ]]; then
    COMPOSE_FILE=${PROD_COMPOSE_FILE}
    echo "📌 Running in PRODUCTION mode"
else
    COMPOSE_FILE=${DEV_COMPOSE_FILE}
    echo "📌 Running in DEVELOPMENT mode"
fi

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Error: Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            echo "❌ Error: Neither docker-compose nor docker compose plugin is available."
            exit 1
        fi
    fi
}

# Function to display usage
show_usage() {
  echo "Scheduler Web Server Control Script"
  echo ""
  echo "Usage: ./run-scheduler.sh [--dev|--prod] [command]"
  echo ""
  echo "Mode selection:"
  echo "  --dev       - Run in development mode (default)"
  echo "  --prod      - Run in production mode"
  echo ""
  echo "Commands:"
  echo "  start      - Start the scheduler application"
  echo "  stop       - Stop the running containers"
  echo "  restart    - Restart the application"
  echo "  logs       - View logs from the web container"
  echo "  status     - Check if containers are running"
  echo "  shell      - Get a shell in the web container"
  echo "  clean      - Stop containers and remove volumes (data will be lost)"
  echo "  build      - Build/rebuild the containers"
  echo "  setup      - First-time setup (create directories, etc.)"
  echo ""
}

# Make sure Docker is available before running any commands
check_docker

# Handle commands
case "$1" in
  start)
    echo "Starting the Scheduler application..."
    docker-compose -f ${COMPOSE_FILE} up -d
    echo "Application started! Access it at http://localhost:8080"
    ;;
    
  stop)
    echo "Stopping the Scheduler application..."
    docker-compose -f ${COMPOSE_FILE} down
    echo "Application stopped."
    ;;
    
  restart)
    echo "Restarting the Scheduler application..."
    docker-compose -f ${COMPOSE_FILE} down
    docker-compose -f ${COMPOSE_FILE} up -d
    echo "Application restarted! Access it at http://localhost:8080"
    ;;
    
  logs)
    if [[ "$2" == "" ]]; then
      echo "Showing logs from all containers (Ctrl+C to exit)..."
      docker-compose -f ${COMPOSE_FILE} logs -f
    else
      echo "Showing logs from $2 container (Ctrl+C to exit)..."
      docker-compose -f ${COMPOSE_FILE} logs -f $2
    fi
    ;;
    
  status)
    echo "Current status of containers:"
    docker-compose -f ${COMPOSE_FILE} ps
    ;;
    
  shell)
    echo "Opening shell in web container..."
    docker-compose -f ${COMPOSE_FILE} exec web /bin/bash
    ;;
    
  build)
    echo "Building/rebuilding containers..."
    docker-compose -f ${COMPOSE_FILE} build
    echo "Build complete! Use './run-scheduler.sh start' to start the application."
    ;;
    
  setup)
    echo "Setting up the Scheduler application for first-time use..."
    
    # Create necessary directories
    mkdir -p data/logs data/static data/media data/postgres data/redis
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
      if [ -f .env.example ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "✅ Created .env file. You may want to edit it with your settings."
      else
        echo "⚠️ Warning: .env.example file not found. You'll need to create a .env file manually."
      fi
    fi
    
    echo "Setup complete! Use './run-scheduler.sh start' to start the application."
    ;;
    
  clean)
    echo "⚠️ WARNING: This will remove all data volumes. Data will be LOST."
    read -p "Are you sure you want to continue? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
      echo "Stopping containers and removing volumes..."
      docker-compose -f ${COMPOSE_FILE} down -v
      echo "Cleanup complete."
    else
      echo "Operation canceled."
    fi
    ;;
    
  help|--help|-h)
    show_usage
    ;;
    
  *)
    if [ -z "$1" ]; then
      show_usage
      echo "No command specified. Use './run-scheduler.sh help' for usage information."
    else
      echo "❌ Unknown command: $1"
      show_usage
    fi
    exit 1
    ;;
esac
