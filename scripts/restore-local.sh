#!/bin/bash
set -e

BACKUP_FILE="${1:-backup.sql}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "🔐 Fetching database credentials from AWS Secrets Manager..."

# Get DB endpoint from Terraform
DB_HOST="sentinel-v2-dev-db.c4lgeom289vc.us-east-1.rds.amazonaws.com"
DB_NAME="sentinelmas"
DB_USER="postgres"
DB_PASSWORD="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4"

echo "📍 Restoring to: $DB_HOST/$DB_NAME"
echo "📂 From file: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"
echo ""

export PGPASSWORD="$DB_PASSWORD"

# Show progress
echo "🔄 Starting restore..."
psql -h "$DB_HOST" \
     -U "$DB_USER" \
     -d "$DB_NAME" \
     -f "$BACKUP_FILE" \
     --set ON_ERROR_STOP=on \
     -v ON_ERROR_ROLLBACK=on

unset PGPASSWORD

echo ""
echo "✅ Restore completed successfully!"