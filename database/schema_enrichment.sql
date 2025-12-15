-- Add enrichment fields to items table

-- Product identification
ALTER TABLE items ADD COLUMN IF NOT EXISTS asin VARCHAR(20);
ALTER TABLE items ADD COLUMN IF NOT EXISTS model VARCHAR(100);

-- Enrichment metadata
ALTER TABLE items ADD COLUMN IF NOT EXISTS enriched BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS enrichment_source VARCHAR(50);
ALTER TABLE items ADD COLUMN IF NOT EXISTS msrp_verified BOOLEAN DEFAULT FALSE;

-- Market data
ALTER TABLE items ADD COLUMN IF NOT EXISTS current_market_price DECIMAL(10, 2);
ALTER TABLE items ADD COLUMN IF NOT EXISTS condition VARCHAR(50) DEFAULT 'Unknown';
ALTER TABLE items ADD COLUMN IF NOT EXISTS category VARCHAR(255);

-- Product details
ALTER TABLE items ADD COLUMN IF NOT EXISTS features TEXT;  -- JSON array of features
ALTER TABLE items ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_items_asin ON items(asin);
CREATE INDEX IF NOT EXISTS idx_items_enriched ON items(enriched);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);

-- Update existing items to have default enrichment values
UPDATE items SET enriched = FALSE WHERE enriched IS NULL;
UPDATE items SET enrichment_source = 'None' WHERE enrichment_source IS NULL;
UPDATE items SET msrp_verified = FALSE WHERE msrp_verified IS NULL;

