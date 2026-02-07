#!/bin/bash

# SensusAI Database Restore Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"
CONTAINER_NAME="sensusai-postgresql-1"
DB_USER="kam_user"
DB_NAME="kam_alerts"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  SensusAI Database Restore${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

# List available backups
echo -e "${BLUE}Available backups:${NC}"
ls -1 "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | nl

# Count backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No backups found${NC}"
    exit 1
fi

# Get backup file
if [ -z "$1" ]; then
    echo ""
    read -p "Enter backup number to restore (or path to backup file): " BACKUP_SELECTION

    if [[ "$BACKUP_SELECTION" =~ ^[0-9]+$ ]]; then
        BACKUP_FILE=$(ls -1 "$BACKUP_DIR"/backup_*.sql.gz | sed -n "${BACKUP_SELECTION}p")
    else
        BACKUP_FILE="$BACKUP_SELECTION"
    fi
else
    BACKUP_FILE="$1"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⚠️  WARNING: This will replace the current database!${NC}"
echo -e "Backup file: ${BLUE}$BACKUP_FILE${NC}"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled${NC}"
    exit 0
fi

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting restore...${NC}"

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${BLUE}Decompressing backup...${NC}"
    TEMP_FILE="/tmp/restore_temp.sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
else
    TEMP_FILE="$BACKUP_FILE"
fi

# Drop existing connections
echo -e "${BLUE}Dropping existing connections...${NC}"
docker exec -t "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

# Drop and recreate database
echo -e "${BLUE}Recreating database...${NC}"
docker exec -t "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" > /dev/null
docker exec -t "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" > /dev/null

# Restore database
echo -e "${BLUE}Restoring database...${NC}"
cat "$TEMP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null

# Clean up temp file
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f "$TEMP_FILE"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restored successfully${NC}"

    # Verify restore
    echo ""
    echo -e "${BLUE}Verifying restore...${NC}"
    TABLE_COUNT=$(docker exec -t "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

    echo -e "Tables restored: ${YELLOW}$TABLE_COUNT${NC}"

else
    echo -e "${RED}❌ Restore failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Restore completed successfully!${NC}"
