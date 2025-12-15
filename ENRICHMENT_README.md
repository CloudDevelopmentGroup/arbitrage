# Data Enrichment & Normalization Feature

## Overview

The system now automatically enriches and normalizes product data from CSV uploads before AI analysis. This ensures consistent, high-quality data regardless of the input CSV format.

## What It Does

### 1. **Product Lookup & Enrichment**
- **Amazon PAAPI - By Code**: Looks up products by UPC/ASIN for exact matches
- **Amazon PAAPI - By Search**: Searches Amazon by product title/description (NEW!)
- **UPC Database**: Fallback lookup service for products not on Amazon
- **Enriches**: Title, brand, category, current market price, product images, features, ASIN

**Search Priority:**
1. ASIN (if available)
2. UPC (if available)
3. **Product Title/Description Search** ← Works with Grainger items!
4. UPC Database (fallback)

### 2. **Data Normalization**
- **Text Cleaning**: Removes HTML tags, extra whitespace, special characters
- **Brand Standardization**: Maps brand aliases (e.g., "HP" vs "Hewlett-Packard")
- **Condition Mapping**: Standardizes condition descriptions (New, Used, Refurbished, etc.)
- **Model Extraction**: Automatically extracts model numbers from titles

### 3. **Price Validation**
- **MSRP Verification**: Cross-checks provided MSRP against Amazon list price
- **Market Price Tracking**: Stores current Amazon price for comparison
- **Outlier Detection**: Flags unrealistic prices in logs

### 4. **Standardized Schema**
All items are converted to a consistent format:
```json
{
  "item_id": "unique-identifier",
  "upc": "012345678901",
  "asin": "B08N5WRWNW",
  "title": "Normalized Product Title",
  "brand": "Standardized Brand",
  "model": "MODEL-123",
  "category": "Electronics > Headphones",
  "msrp": 349.99,
  "msrp_verified": true,
  "current_market_price": 278.00,
  "quantity": 5,
  "condition": "New",
  "image_url": "https://...",
  "features": ["Feature 1", "Feature 2"],
  "enriched": true,
  "enrichment_source": "Amazon ASIN"
}
```

## Database Schema

New fields added to `items` table:
- `asin` - Amazon product ID
- `model` - Product model number
- `enriched` - Boolean flag indicating if enrichment was successful
- `enrichment_source` - Where the data came from (Amazon ASIN, UPC Database, etc.)
- `msrp_verified` - Boolean flag indicating if MSRP was verified
- `current_market_price` - Current Amazon price
- `condition` - Product condition (New, Used, etc.)
- `category` - Product category
- `features` - JSON array of product features
- `image_url` - Product image URL

## Processing Flow

```
1. CSV Upload
   ↓
2. Parse CSV (format-specific parsing)
   ↓
3. Enrich & Normalize (NEW!)
   - Lookup by UPC/ASIN on Amazon
   - Fallback to UPC Database
   - Normalize text, brands, conditions
   - Extract model numbers
   - Validate MSRP
   ↓
4. Queue to SQS for AI Analysis
   ↓
5. AI Analysis (now uses enriched data!)
   - Better prompts with verified data
   - Market price context
   - Product features for accuracy
   ↓
6. Save to Database (with enriched fields)
```

## Benefits

1. **Better AI Analysis**: AI gets verified product data and current market prices
2. **Format Independence**: Handles any CSV format - standardizes everything
3. **Price Accuracy**: Validates MSRP and provides market context
4. **Data Quality**: Cleans and normalizes all text data
5. **Debugging**: Easy to see which items were enriched and from where

## Configuration

### Required Environment Variables:
- `GROQ_API_KEY` - For AI analysis
- `AMAZON_ACCESS_KEY` - For Amazon PAAPI (optional but recommended)
- `AMAZON_SECRET_KEY` - For Amazon PAAPI
- `AMAZON_PARTNER_TAG` - Amazon partner tag (default: sndflo-20)
- `AMAZON_REGION` - AWS region (default: us-east-1)

### Enrichment Settings:
- **Parallel Workers**: 10 concurrent enrichment lookups
- **Timeout**: 5 seconds per API call
- **Fallback**: If Amazon fails, tries UPC Database
- **Graceful Degradation**: If all lookups fail, uses raw parsed data

## Monitoring

Check CloudWatch logs for:
- `Enrichment complete: X items successfully enriched` - Success rate
- `MSRP mismatch: ... using external` - Price validation corrections
- `Amazon lookup successful for ...` - Successful enrichments
- `Failed to enrich item ...` - Enrichment failures

## Performance

- **Speed**: ~10 items/second with parallel processing
- **Cache**: Could add caching layer for repeated UPCs (future enhancement)
- **Cost**: Amazon PAAPI is free up to 8,640 requests/day

## Testing

Upload a CSV with products that have UPCs or ASINs. Check the database:

```sql
SELECT 
  item_number, 
  title, 
  enriched, 
  enrichment_source, 
  msrp_verified,
  current_market_price,
  category
FROM items 
WHERE manifest_id = 'your-manifest-id'
LIMIT 10;
```

Look for:
- `enriched = true` - Item was successfully enriched
- `enrichment_source` - Shows where data came from
- `msrp_verified = true` - MSRP was cross-checked
- `current_market_price` - Has current Amazon price

## Future Enhancements

1. **Caching**: Cache enrichment results by UPC to avoid repeated lookups
2. **More Sources**: Add Google Shopping API, Walmart API, etc.
3. **Category AI**: Use AI to classify products without category data
4. **Historical Pricing**: Track price changes over time
5. **Image Analysis**: Use computer vision to extract product details from images
6. **Bulk API**: Batch API calls for better performance

