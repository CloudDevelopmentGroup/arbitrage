import json
import os
import logging
from csv_processor_async import (
    analyze_item_with_ai,
    analyze_item_mock,
    get_db_connection
)
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Database connection parameters
DB_CONFIG = {
    'host': None,
    'database': None,
    'user': None,
    'password': None,
    'port': 5432
}

def lambda_handler(event, context):
    """
    Lambda handler for checking individual items
    Accepts item details and returns analysis without storing to database
    """
    
    # CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Max-Age': '86400'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }
    
    try:
        # Set database config from environment (optional for single item check)
        try:
            db_host = os.environ.get('DB_HOST')
            if db_host:
                if ':' in db_host:
                    host, port = db_host.split(':')
                    DB_CONFIG['host'] = host
                    DB_CONFIG['port'] = int(port)
                else:
                    DB_CONFIG['host'] = db_host
                DB_CONFIG['database'] = os.environ.get('DB_NAME')
                DB_CONFIG['user'] = os.environ.get('DB_USER')
                DB_CONFIG['password'] = os.environ.get('DB_PASSWORD')
        except Exception as db_config_error:
            logger.warning(f"DB config not available: {str(db_config_error)}")
        
        # Parse the request body
        if 'body' in event:
            body = event['body']
            if event.get('isBase64Encoded', False):
                import base64
                body = base64.b64decode(body).decode('utf-8')
            
            try:
                body_data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'error': 'Invalid JSON body'})
                }
        else:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'No request body provided'})
            }
        
        # Extract item details from request
        item_number = body_data.get('item_number', '').strip()
        title = body_data.get('title', '').strip()
        msrp_str = str(body_data.get('msrp', '0')).replace('$', '').replace(',', '').strip()
        quantity = body_data.get('quantity', 1)
        notes = body_data.get('notes', '').strip() if body_data.get('notes') else None
        
        # Validate required fields
        if not title:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Item title is required'})
            }
        
        # Parse MSRP
        try:
            msrp = float(msrp_str) if msrp_str else 0.0
        except ValueError:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Invalid MSRP value'})
            }
        
        if msrp <= 0:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'MSRP must be greater than 0'})
            }
        
        # Parse quantity
        try:
            quantity = int(quantity)
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        
        # Build item object
        item = {
            'item_number': item_number or 'N/A',
            'title': title,
            'msrp': msrp,
            'quantity': quantity,
            'notes': notes
        }
        
        logger.info(f"Analyzing single item: {item['title']} (MSRP: ${msrp})")
        
        # Analyze the item
        try:
            analysis = analyze_item_with_ai(item)
            logger.info(f"AI analysis successful for item: {item['title']}")
        except Exception as ai_error:
            logger.warning(f"AI API unavailable, using mock analysis: {str(ai_error)}")
            analysis = analyze_item_mock(item)
        
        # Calculate profit based on estimated sale price
        estimated_sale_price = float(analysis.get('estimatedSalePrice', 0))
        # Purchase price is 30% of projected resale value
        purchase_price = estimated_sale_price * 0.30
        profit_per_item = estimated_sale_price - purchase_price
        total_investment = purchase_price * quantity
        total_revenue = estimated_sale_price * quantity
        total_profit = profit_per_item * quantity
        
        # Calculate ROI
        roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
        
        # Build response
        response_data = {
            'item': {
                'item_number': item['item_number'],
                'title': item['title'],
                'msrp': msrp,
                'quantity': quantity,
                'notes': notes
            },
            'analysis': {
                'estimatedSalePrice': estimated_sale_price,
                'purchasePrice': round(purchase_price, 2),
                'profitPerItem': round(profit_per_item, 2),
                'demand': analysis.get('demand', 'Unknown'),
                'salesTime': analysis.get('salesTime', 'Unknown'),
                'reasoning': analysis.get('reasoning', 'No reasoning provided'),
                'profitMargin': analysis.get('profitMargin', 0)
            },
            'summary': {
                'totalInvestment': round(total_investment, 2),
                'totalRevenue': round(total_revenue, 2),
                'totalProfit': round(total_profit, 2),
                'roi': round(roi, 2),
                'quantity': quantity
            }
        }
        
        logger.info(f"Successfully analyzed item: {item['title']}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing item: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

