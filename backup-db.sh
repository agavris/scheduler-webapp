#!/bin/bash
# PostgreSQL database backup script for scheduler application
# Recommended to run as a cron job daily

# Exit on error
set -e

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$(dirname "$0")/backups"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment variables from .env
if [ -f "$(dirname "$0")/.env" ]; then
  source "$(dirname "$0")/.env"
fi

# Log function
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting database backup..."

# Backup PostgreSQL database
DB_CONTAINER=$(docker ps -qf "name=scheduler-web.*db" | head -n 1)

if [ -z "$DB_CONTAINER" ]; then
  log "ERROR: Database container not found!"
  exit 1
fi

log "Using database container: $DB_CONTAINER"

# Create SQL dump
BACKUP_FILE="$BACKUP_DIR/scheduler_$TIMESTAMP.sql"
log "Creating SQL dump to $BACKUP_FILE"
docker exec -t "$DB_CONTAINER" pg_dump -U postgres scheduler > "$BACKUP_FILE"

# Compress the backup
log "Compressing backup file..."
gzip "$BACKUP_FILE"
log "Backup created: $BACKUP_FILE.gz"

# Remove backups older than retention period
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "scheduler_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# Copy latest backup to a stable filename for easy access
cp "$BACKUP_FILE.gz" "$BACKUP_DIR/latest_backup.sql.gz"

log "Backup completed successfully!"

# Optional: Upload to remote storage (uncomment and configure as needed)
# if [ -n "$S3_BUCKET" ]; then
#   log "Uploading backup to S3..."
#   aws s3 cp "$BACKUP_FILE.gz" "s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE.gz")"
#   log "Upload complete!"
# fi
