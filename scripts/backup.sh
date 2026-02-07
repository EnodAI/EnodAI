#!/bin/bash

# SensusAI Database Backup Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="sensusai-postgresql-1"
DB_USER="kam_user"
DB_NAME="kam_alerts"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  SensusAI Database Backup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    exit 1
fi

echo -e "${BLUE}Starting backup...${NC}"

# Backup database
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database backup completed${NC}"
    echo -e "Backup file: ${YELLOW}$BACKUP_FILE${NC}"

    # Compress backup
    gzip "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup compressed${NC}"
    echo -e "Compressed file: ${YELLOW}${BACKUP_FILE}.gz${NC}"

    # Get file size
    SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo -e "File size: ${YELLOW}${SIZE}${NC}"

    # Clean old backups (keep last 7 days)
    echo ""
    echo -e "${BLUE}Cleaning old backups...${NC}"
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
    echo -e "${GREEN}✅ Old backups cleaned${NC}"

    # List backups
    echo ""
    echo -e "${BLUE}Available backups:${NC}"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz | awk '{print "  " $9 " (" $5 ")"}'

else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
