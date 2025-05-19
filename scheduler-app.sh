#!/bin/bash
set -e

# Scheduler Application Launcher
# This script provides a simple way to manage the Scheduler application

# Default configuration
APP_NAME="Scheduler Application"
PORT=8080
DATA_DIR="./data"
COMPOSE_FILE="docker-compose.yml"

# Display banner
show_banner() {
    echo "========================================"
    echo "     ${APP_NAME} Manager"
    echo "========================================"
    echo "Access the application at: http://localhost:${PORT}"
    echo "========================================"
}

# Check for Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker to run this application."
        echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Error: Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    echo "✓ Docker is installed and running"
}

# Check for Docker Compose
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "Warning: docker-compose command not found. Using docker compose plugin..."
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
        echo "✓ Docker Compose is installed"
    fi
}

# Setup first-time configuration
setup() {
    echo "Setting up ${APP_NAME} for first use..."
    
    # Create data directory if it doesn't exist
    mkdir -p "${DATA_DIR}"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "✓ Created .env file from template"
            echo "You may want to edit the .env file to customize settings."
        else
            echo "Error: .env.example file not found."
            exit 1
        fi
    fi
    
    # Load pre-built images if they exist
    if [ -d "images" ]; then
        echo "Loading pre-built Docker images..."
        for image in images/*.tar; do
            if [ -f "$image" ]; then
                echo "Loading image: $image"
                docker load -i "$image"
            fi
        done
    fi
    
    echo "✓ Setup completed"
}

# Start the application
start() {
    echo "Starting ${APP_NAME}..."
    $COMPOSE_CMD -f "${COMPOSE_FILE}" up -d
    echo "✓ Application started!"
    echo "  Access it at http://localhost:${PORT}"
}

# Stop the application
stop() {
    echo "Stopping ${APP_NAME}..."
    $COMPOSE_CMD -f "${COMPOSE_FILE}" down
    echo "✓ Application stopped"
}

# Restart the application
restart() {
    stop
    start
}

# Show logs
logs() {
    echo "Showing logs for ${APP_NAME}..."
    $COMPOSE_CMD -f "${COMPOSE_FILE}" logs -f
}

# Show status of containers
status() {
    echo "Status of ${APP_NAME} containers:"
    $COMPOSE_CMD -f "${COMPOSE_FILE}" ps
}

# Show help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup      - Set up the application for first use"
    echo "  start      - Start the application"
    echo "  stop       - Stop the application"
    echo "  restart    - Restart the application"
    echo "  logs       - Show application logs"
    echo "  status     - Show container status"
    echo "  help       - Show this help message"
    echo ""
    echo "If no command is provided, the application will be started."
}

# Main script execution
show_banner
check_docker
check_compose

# Process command
case "$1" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    help)
        show_help
        ;;
    *)
        # If no argument provided or unrecognized, start the app
        # But first make sure it's set up
        if [ ! -f .env ]; then
            setup
        fi
        start
        ;;
esac

exit 0
