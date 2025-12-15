"""
Data Enrichment and Normalization Module

This module enriches product data from various CSV formats into a standardized schema.
It performs:
- Product lookup via UPC/ASIN (Amazon PAAPI, UPC databases)
- Data normalization (text cleaning, brand standardization)
- Price validation and verification
- Category classification
"""

import re
import os
import logging
from decimal import Decimal
import requests

# Import Amazon PAAPI (optional - graceful degradation if not available)
try:
    from amazon_paapi import AmazonApi
    AmazonAPI = AmazonApi  # Alias for consistency
except ImportError:
    AmazonAPI = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Brand normalization mappings
BRAND_ALIASES = {
    'hp': 'HP',
    'hewlett packard': 'HP',
    'hewlett-packard': 'HP',
    'dell': 'Dell',
    'lenovo': 'Lenovo',
    'microsoft': 'Microsoft',
    'ms': 'Microsoft',
    'sony': 'Sony',
    'samsung': 'Samsung',
    'lg': 'LG',
    'apple': 'Apple',
    'intel': 'Intel',
    'amd': 'AMD',
    # Add more as needed
}

# Condition normalization
CONDITION_MAPPING = {
    'new': 'New',
    'brand new': 'New',
    'factory sealed': 'New',
    'like new': 'Like New',
    'refurbished': 'Refurbished',
    'renewed': 'Refurbished',
    'used': 'Used',
    'open box': 'Open Box',
    'damaged': 'Damaged',
}

def normalize_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters but keep alphanumeric, spaces, and basic punctuation
    text = re.sub(r'[^\w\s\-.,()\/]', '', text)
    
    return text

def normalize_brand(brand):
    """Normalize brand names"""
    if not brand:
        return None
    
    brand_lower = brand.lower().strip()
    return BRAND_ALIASES.get(brand_lower, brand.title())

def normalize_condition(condition):
    """Normalize condition descriptions"""
    if not condition:
        return 'Unknown'
    
    condition_lower = condition.lower().strip()
    return CONDITION_MAPPING.get(condition_lower, 'Unknown')

def extract_model_number(title, brand=None):
    """Extract model number from title"""
    if not title:
        return None
    
    # Common model patterns
    patterns = [
        r'\b[A-Z]{2,}\-?\d{3,}\b',  # e.g., WH-1000XM4, HP-2550
        r'\b[A-Z]\d{3,}[A-Z]?\b',   # e.g., T480s, X1
        r'\b\d{3,}[A-Z]{1,3}\b',    # e.g., 3070Ti, 5600X
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(0)
    
    return None

def lookup_amazon_product(identifier, identifier_type='UPC'):
    """
    Lookup product on Amazon using PAAPI
    
    Args:
        identifier: UPC, ASIN, or EAN
        identifier_type: 'UPC', 'ASIN', or 'EAN'
    
    Returns:
        dict with product data or None
    """
    try:
        # Check if Amazon API is available
        if AmazonAPI is None:
            logger.warning("Amazon PAAPI module not available")
            return None
        
        # Get Amazon credentials from Secrets Manager or environment
        access_key = os.environ.get('AMAZON_ACCESS_KEY')
        secret_key = os.environ.get('AMAZON_SECRET_KEY')
        partner_tag = os.environ.get('AMAZON_PARTNER_TAG', 'sndflo-20')
        region = os.environ.get('AMAZON_REGION', 'us-east-1')
        
        if not access_key or not secret_key:
            logger.warning("Amazon PAAPI credentials not configured")
            return None
        
        # Initialize Amazon API
        amazon = AmazonAPI(access_key, secret_key, partner_tag, region)
        
        # Search by identifier
        if identifier_type == 'ASIN':
            items = amazon.get_items([identifier])
        else:
            # Search by UPC/EAN
            items = amazon.search_items(keywords=identifier, search_index='All')
        
        if not items or len(items) == 0:
            return None
        
        item = items[0]
        
        # Extract product data
        product_data = {
            'asin': item.asin if hasattr(item, 'asin') else None,
            'title': item.item_info.title.display_value if hasattr(item.item_info, 'title') else None,
            'brand': item.item_info.by_line_info.brand.display_value if hasattr(item.item_info, 'by_line_info') else None,
            'list_price': None,
            'current_price': None,
            'image_url': None,
            'category': None,
            'features': [],
        }
        
        # Extract prices
        if hasattr(item, 'offers') and item.offers:
            listings = item.offers.listings
            if listings and len(listings) > 0:
                listing = listings[0]
                if hasattr(listing, 'price'):
                    product_data['current_price'] = float(listing.price.amount) if listing.price else None
                if hasattr(listing, 'saving_basis'):
                    product_data['list_price'] = float(listing.saving_basis.amount) if listing.saving_basis else None
        
        # Extract images
        if hasattr(item, 'images') and item.images:
            primary_image = item.images.primary
            if primary_image and hasattr(primary_image, 'large'):
                product_data['image_url'] = primary_image.large.url
        
        # Extract category
        if hasattr(item.item_info, 'classifications'):
            binding = item.item_info.classifications.binding
            product_data['category'] = binding.display_value if binding else None
        
        # Extract features
        if hasattr(item.item_info, 'features'):
            features = item.item_info.features
            if features and hasattr(features, 'display_values'):
                product_data['features'] = features.display_values[:5]  # Top 5 features
        
        logger.info(f"Amazon lookup successful for {identifier}: {product_data.get('title', 'Unknown')[:50]}")
        return product_data
        
    except Exception as e:
        logger.warning(f"Amazon lookup failed for {identifier}: {str(e)}")
        return None

def search_amazon_by_title(title, brand=None):
    """
    Search Amazon by product title/description
    
    Args:
        title: Product title or description
        brand: Optional brand name to refine search
    
    Returns:
        dict with product data or None
    """
    try:
        # Check if Amazon API is available
        if AmazonAPI is None:
            logger.warning("Amazon PAAPI module not available")
            return None
        
        # Get Amazon credentials
        access_key = os.environ.get('AMAZON_ACCESS_KEY')
        secret_key = os.environ.get('AMAZON_SECRET_KEY')
        partner_tag = os.environ.get('AMAZON_PARTNER_TAG', 'sndflo-20')
        region = os.environ.get('AMAZON_REGION', 'us-east-1')
        
        if not access_key or not secret_key:
            logger.warning("Amazon PAAPI credentials not configured")
            return None
        
        # Initialize Amazon API
        amazon = AmazonAPI(access_key, secret_key, partner_tag, region)
        
        # Clean and prepare search query
        # Extract key product identifiers from title
        search_query = title[:100]  # Limit to first 100 chars for better results
        
        # If brand is known, include it in search
        if brand:
            search_query = f"{brand} {search_query}"
        
        logger.info(f"Searching Amazon for: {search_query[:50]}...")
        
        # Search Amazon - use 'All' category for broad search
        items = amazon.search_items(keywords=search_query, search_index='All', item_count=3)
        
        if not items or len(items) == 0:
            logger.info(f"No Amazon results for: {search_query[:50]}")
            return None
        
        # Take the first (best match) result
        item = items[0]
        
        # Extract product data (same as lookup_amazon_product)
        product_data = {
            'asin': item.asin if hasattr(item, 'asin') else None,
            'title': item.item_info.title.display_value if hasattr(item.item_info, 'title') else None,
            'brand': item.item_info.by_line_info.brand.display_value if hasattr(item.item_info, 'by_line_info') else None,
            'list_price': None,
            'current_price': None,
            'image_url': None,
            'category': None,
            'features': [],
        }
        
        # Extract prices
        if hasattr(item, 'offers') and item.offers:
            listings = item.offers.listings
            if listings and len(listings) > 0:
                listing = listings[0]
                if hasattr(listing, 'price'):
                    product_data['current_price'] = float(listing.price.amount) if listing.price else None
                if hasattr(listing, 'saving_basis'):
                    product_data['list_price'] = float(listing.saving_basis.amount) if listing.saving_basis else None
        
        # Extract images
        if hasattr(item, 'images') and item.images:
            primary_image = item.images.primary
            if primary_image and hasattr(primary_image, 'large'):
                product_data['image_url'] = primary_image.large.url
        
        # Extract category
        if hasattr(item.item_info, 'classifications'):
            binding = item.item_info.classifications.binding
            product_data['category'] = binding.display_value if binding else None
        
        # Extract features
        if hasattr(item.item_info, 'features'):
            features = item.item_info.features
            if features and hasattr(features, 'display_values'):
                product_data['features'] = features.display_values[:5]
        
        logger.info(f"Amazon search successful: {product_data.get('title', 'Unknown')[:50]}")
        return product_data
        
    except Exception as e:
        logger.warning(f"Amazon search failed for '{title[:50]}': {str(e)}")
        return None

def ai_find_amazon_asin(title, brand=None):
    """
    Use AI to find the Amazon ASIN for a product based on its description
    
    Args:
        title: Product title/description
        brand: Optional brand name
    
    Returns:
        dict with ASIN and estimated current price, or None
    """
    try:
        # Get API keys from csv_processor module
        from csv_processor import get_api_keys
        api_keys = get_api_keys()
        
        groq_api_key = api_keys.get('GROQ_API_KEY')
        openai_api_key = api_keys.get('OPENAI_API_KEY')
        
        if groq_api_key:
            api_key = groq_api_key
            api_url = 'https://api.groq.com/openai/v1/chat/completions'
            model = 'llama-3.3-70b-versatile'
        elif openai_api_key:
            api_key = openai_api_key
            api_url = 'https://api.openai.com/v1/chat/completions'
            model = 'gpt-4'
        else:
            return None
        
        # Create search query
        search_query = f"{brand} {title}" if brand else title
        search_query = search_query[:150]  # Limit length
        
        # AI prompt to find ASIN
        prompt = f"""Find the Amazon ASIN for this product: {search_query}

Based on your knowledge, what is the most likely Amazon ASIN for this product? Also estimate its current Amazon price.

Respond ONLY with valid JSON:
{{
    "asin": "B0XXXXXXX",
    "current_price": 299.99,
    "confidence": "high/medium/low"
}}

If you cannot determine the ASIN, respond with: {{"asin": null, "current_price": null, "confidence": "none"}}"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are an expert at identifying Amazon products and their ASINs.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.1,  # Low temperature for factual responses
            'max_tokens': 150
        }
        
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Clean JSON markers
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            import json as json_module
            ai_result = json_module.loads(content)
            
            if ai_result.get('asin') and ai_result.get('confidence') in ['high', 'medium']:
                logger.info(f"AI found ASIN {ai_result['asin']} for: {search_query[:50]}")
                return {
                    'asin': ai_result['asin'],
                    'current_price': ai_result.get('current_price'),
                    'enrichment_source': 'AI ASIN Lookup'
                }
        
        return None
        
    except Exception as e:
        logger.warning(f"AI ASIN lookup failed for '{title[:50]}': {str(e)}")
        return None

def lookup_upc_database(upc):
    """
    Lookup product in UPC database (fallback if Amazon fails)
    Using UPCitemdb.com API (free tier)
    """
    try:
        # Note: This is a free API, consider upgrading for production
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={upc}"
        
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if data.get('code') != 'OK' or not data.get('items'):
            return None
        
        item = data['items'][0]
        
        return {
            'title': item.get('title'),
            'brand': item.get('brand'),
            'category': item.get('category'),
            'image_url': item.get('images', [None])[0] if item.get('images') else None,
            'upc': upc,
        }
        
    except Exception as e:
        logger.warning(f"UPC database lookup failed for {upc}: {str(e)}")
        return None

def enrich_product(raw_item):
    """
    Main enrichment function - takes raw parsed item and returns enriched standardized item
    
    Args:
        raw_item: dict with fields like {item_number, title, msrp, upc, brand, quantity}
    
    Returns:
        dict with standardized enriched product data
    """
    logger.info(f"Enriching item: {raw_item.get('item_number', 'unknown')}")
    
    # Start with normalized raw data
    enriched = {
        'item_id': raw_item.get('item_number'),
        'item_number': raw_item.get('item_number'),  # Keep for compatibility
        'upc': raw_item.get('upc'),
        'asin': raw_item.get('asin'),
        'title': normalize_text(raw_item.get('title', '')),
        'brand': normalize_brand(raw_item.get('brand')),
        'model': raw_item.get('model'),
        'category': raw_item.get('category'),
        'msrp': float(raw_item.get('msrp', 0)),
        'msrp_verified': False,
        'current_market_price': None,
        'quantity': int(raw_item.get('quantity', 1)),
        'condition': normalize_condition(raw_item.get('condition')),
        'image_url': None,
        'features': [],
        'enriched': False,
        'enrichment_source': None,
    }
    
    # Try to enrich from external sources
    external_data = None
    
    # Use AI to find Amazon ASIN based on product description (if enabled)
    # This is more reliable than Amazon PAAPI in Lambda (no filesystem issues)
    # NOTE: This is slow and uses AI API calls, so it's optional
    enable_ai_asin_lookup = os.environ.get('ENABLE_AI_ASIN_LOOKUP', 'false').lower() == 'true'
    
    if enable_ai_asin_lookup and enriched['title'] and not enriched['asin']:
        external_data = ai_find_amazon_asin(enriched['title'], enriched.get('brand'))
        if external_data and external_data.get('asin'):
            # Update enrichment metadata
            if not enriched['asin']:
                enriched['asin'] = external_data['asin']
            if external_data.get('current_price') and not enriched['current_market_price']:
                enriched['current_market_price'] = external_data['current_price']
            enriched['enriched'] = True
            enriched['enrichment_source'] = external_data.get('enrichment_source', 'AI ASIN Lookup')
    
    # Merge external data (prefer external data when available)
    if external_data:
        enriched['enriched'] = True
        
        # Use external title if original is poor quality or missing
        if external_data.get('title') and (
            not enriched['title'] or 
            len(enriched['title']) < 20 or
            enriched['title'].isupper()  # All caps titles are usually low quality
        ):
            enriched['title'] = normalize_text(external_data['title'])
        
        # Use external brand if missing
        if external_data.get('brand') and not enriched['brand']:
            enriched['brand'] = normalize_brand(external_data['brand'])
        
        # Add ASIN if found
        if external_data.get('asin') and not enriched['asin']:
            enriched['asin'] = external_data['asin']
        
        # Verify MSRP against list price
        if external_data.get('list_price'):
            enriched['msrp_verified'] = True
            # If our MSRP is way off, use the external one
            if enriched['msrp'] == 0 or abs(enriched['msrp'] - external_data['list_price']) > enriched['msrp'] * 0.5:
                logger.info(f"MSRP mismatch: {enriched['msrp']} vs {external_data['list_price']}, using external")
                enriched['msrp'] = external_data['list_price']
        
        # Add current market price
        if external_data.get('current_price'):
            enriched['current_market_price'] = external_data['current_price']
        
        # Add image
        if external_data.get('image_url'):
            enriched['image_url'] = external_data['image_url']
        
        # Add category
        if external_data.get('category') and not enriched['category']:
            enriched['category'] = external_data['category']
        
        # Add features
        if external_data.get('features'):
            enriched['features'] = external_data['features']
    
    # Extract model number if not present
    if not enriched['model']:
        enriched['model'] = extract_model_number(enriched['title'], enriched['brand'])
    
    # Validate final data
    if not enriched['title'] or len(enriched['title']) < 3:
        logger.warning(f"Item {enriched['item_id']} has invalid title after enrichment")
    
    if enriched['msrp'] <= 0:
        logger.warning(f"Item {enriched['item_id']} has invalid MSRP: {enriched['msrp']}")
    
    logger.info(f"Enrichment complete for {enriched['item_id']}: enriched={enriched['enriched']}, source={enriched['enrichment_source']}")
    
    return enriched

def enrich_batch(raw_items, max_workers=10):
    """
    Enrich multiple items in parallel
    
    Args:
        raw_items: list of raw item dicts
        max_workers: number of parallel workers
    
    Returns:
        list of enriched items
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    enriched_items = []
    
    # Process in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(enrich_product, item): item for item in raw_items}
        
        for future in as_completed(futures):
            try:
                enriched_item = future.result()
                enriched_items.append(enriched_item)
            except Exception as e:
                original_item = futures[future]
                logger.error(f"Failed to enrich item {original_item.get('item_number')}: {str(e)}")
                # Add un-enriched item as fallback
                enriched_items.append({
                    **original_item,
                    'enriched': False,
                    'enrichment_source': 'Failed',
                })
    
    # Sort back to original order
    item_order = {item['item_number']: i for i, item in enumerate(raw_items)}
    enriched_items.sort(key=lambda x: item_order.get(x['item_id'], 999999))
    
    logger.info(f"Enriched {len(enriched_items)} items, {sum(1 for i in enriched_items if i.get('enriched'))} successfully enriched")
    
    return enriched_items

