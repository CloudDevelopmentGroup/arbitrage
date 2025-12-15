#!/usr/bin/env python3
import os
import psycopg2

def lambda_handler(event, context):
    """Run database migration"""
    try:
        # Get database connection
        db_host = os.environ.get('DB_HOST', '')
        if ':' in db_host:
            host, port = db_host.split(':')
            port = int(port)
        else:
            host = db_host
            port = 5432
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=os.environ.get('DB_NAME', 'arbitrage'),
            user=os.environ.get('DB_USER', 'arbitrage_user'),
            password=os.environ.get('DB_PASSWORD', '')
        )
        
        cursor = conn.cursor()
        
        # Run schema migration
        migration_sql = """
-- Add user-friendly name field to uploads
ALTER TABLE uploads 
ADD COLUMN IF NOT EXISTS upload_name VARCHAR(255);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_uploads_upload_name ON uploads(upload_name);

-- Update existing uploads to have default names
UPDATE uploads 
SET upload_name = CONCAT('Upload ', TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS'))
WHERE upload_name IS NULL;
"""
        
        cursor.execute(migration_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': 'Migration completed successfully'
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Migration failed: {str(e)}'
        }

