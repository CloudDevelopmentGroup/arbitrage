-- Add columns for async processing status
ALTER TABLE uploads 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS processed_items INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Add index for status queries
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at DESC);

-- Add unique constraint for manifest items
ALTER TABLE items
ADD CONSTRAINT IF NOT EXISTS items_manifest_item_unique 
UNIQUE (manifest_id, item_number);
