-- Add user-friendly name field to uploads
ALTER TABLE uploads 
ADD COLUMN IF NOT EXISTS upload_name VARCHAR(255);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_uploads_upload_name ON uploads(upload_name);

-- Update existing uploads to have default names
UPDATE uploads 
SET upload_name = CONCAT('Upload ', TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS'))
WHERE upload_name IS NULL;
