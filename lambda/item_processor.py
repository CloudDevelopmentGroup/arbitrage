import json
import os
import boto3
import logging
from csv_processor import (
    analyze_item_with_ai,
    get_db_connection
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Process individual items from SQS queue
    Each message contains one item to analyze
    """
    try:
        # Process each SQS message
        for record in event['Records']:
            try:
                # Parse the message
                message_body = json.loads(record['body'])
                upload_id = message_body['upload_id']
                item_id = message_body['item_id']
                item_index = message_body['item_index']
                total_items = message_body['total_items']
                
                logger.info(f"Processing item {item_index + 1}/{total_items} (ID: {item_id}) for upload {upload_id}")
                
                # Fetch item from database
                conn = get_db_connection()
                if not conn:
                    logger.error("Database connection failed")
                    continue
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, item_number, title, msrp, quantity, status
                    FROM items
                    WHERE id = %s
                """, (item_id,))
                
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not row:
                    logger.error(f"Item {item_id} not found in database")
                    continue
                
                # Build item dict from database
                item = {
                    'id': row[0],
                    'item_number': row[1],
                    'title': row[2],
                    'msrp': row[3],
                    'quantity': row[4],
                    'status': row[5]
                }
                
                # Skip if already processed
                if item['status'] == 'processed':
                    logger.info(f"Item {item_id} already processed, skipping")
                    continue
                
                try:
                    # Analyze the item using existing AI function
                    analysis = analyze_item_with_ai(item)
                    
                    # Calculate profit
                    # Purchase price should be 30% of projected resale value
                    projected_revenue = float(analysis.get('estimatedSalePrice', 0))
                    purchase_price = projected_revenue * 0.30  # Pay 30% of what we expect to sell for
                    profit = projected_revenue - purchase_price
                    
                    # Save results to database
                    save_item_analysis(upload_id, item, analysis, profit)
                    logger.info(f"Successfully processed item {item_index + 1}/{total_items}")
                    
                except Exception as analysis_error:
                    logger.error(f"AI analysis failed for item {item_index + 1}: {str(analysis_error)}")
                    # Save error to database so item is not lost
                    try:
                        save_item_error(upload_id, item, str(analysis_error))
                    except Exception as save_error:
                        logger.error(f"Failed to save error item: {str(save_error)}")
                
                # Always update progress, even if item failed
                try:
                    update_upload_progress(upload_id, item_index + 1, total_items)
                except Exception as progress_error:
                    logger.error(f"Failed to update progress: {str(progress_error)}")
                
            except Exception as item_error:
                logger.error(f"Critical error processing item: {str(item_error)}")
                # Don't raise - let other items process
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Items processed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        raise

def save_item_analysis(upload_id, item, analysis, profit):
    """Save analyzed item to database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            error_msg = "Database connection failed"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        cursor = conn.cursor()
        
        # Get manifest_id from upload
        cursor.execute("SELECT manifest_id FROM uploads WHERE id = %s", (upload_id,))
        result = cursor.fetchone()
        if not result:
            error_msg = f"Upload {upload_id} not found"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        manifest_id = result[0]
        
        # Ensure item has a unique identifier
        item_number = item.get('item_id') or item.get('item_number') or item.get('sku')
        if not item_number:
            # Generate a unique item number if missing
            import hashlib
            item_number = hashlib.md5(item.get('title', 'unknown').encode()).hexdigest()[:12]
            logger.warning(f"Item missing item_number, generated: {item_number}")
        
        logger.info(f"Saving item {item_number} to manifest {manifest_id}")
        
        # Update item with analysis results (item already exists from insert_items_to_database)
        cursor.execute("""
            UPDATE items
            SET estimated_sale_price = %s,
                profit = %s,
                demand = %s,
                sales_time = %s,
                reasoning = %s,
                asin = %s,
                model = %s,
                enriched = %s,
                enrichment_source = %s,
                msrp_verified = %s,
                current_market_price = %s,
                condition = %s,
                category = %s,
                features = %s,
                image_url = %s,
                status = 'processed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            analysis.get('estimatedSalePrice'),
            profit,
            analysis.get('demand'),
            analysis.get('salesTime'),
            analysis.get('reasoning'),
            item.get('asin'),
            item.get('model'),
            item.get('enriched', False),
            item.get('enrichment_source'),
            item.get('msrp_verified', False),
            item.get('current_market_price'),
            item.get('condition', 'Unknown'),
            item.get('category'),
            json.dumps(item.get('features', [])) if item.get('features') else None,
            item.get('image_url'),
            item['id']  # WHERE id = %s
        ))
        
        conn.commit()
        logger.info(f"Successfully saved item {item_number} to database")
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error saving item analysis for {item.get('item_number', 'unknown')}: {str(e)}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        raise

def save_item_error(upload_id, item, error_message):
    """Save item processing error to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        # Get manifest_id
        cursor.execute("SELECT manifest_id FROM uploads WHERE id = %s", (upload_id,))
        result = cursor.fetchone()
        if not result:
            return
        
        manifest_id = result[0]
        
        # Insert item with error
        cursor.execute("""
            INSERT INTO items (
                manifest_id, item_number, title, msrp, quantity,
                estimated_sale_price, profit, demand, sales_time, reasoning,
                asin, model, enriched, enrichment_source, msrp_verified,
                current_market_price, condition, category, features, image_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (manifest_id, item_number) 
            DO UPDATE SET
                reasoning = EXCLUDED.reasoning,
                asin = EXCLUDED.asin,
                model = EXCLUDED.model,
                enriched = EXCLUDED.enriched,
                enrichment_source = EXCLUDED.enrichment_source,
                msrp_verified = EXCLUDED.msrp_verified,
                current_market_price = EXCLUDED.current_market_price,
                condition = EXCLUDED.condition,
                category = EXCLUDED.category,
                features = EXCLUDED.features,
                image_url = EXCLUDED.image_url,
                updated_at = CURRENT_TIMESTAMP
        """, (
            manifest_id,
            item.get('item_id') or item.get('item_number'),
            item.get('title'),
            item.get('msrp'),
            item.get('quantity', 1),
            0,
            0,
            'Error',
            'N/A',
            f'Processing error: {error_message[:200]}',
            item.get('asin'),
            item.get('model'),
            item.get('enriched', False),
            item.get('enrichment_source'),
            item.get('msrp_verified', False),
            item.get('current_market_price'),
            item.get('condition', 'Unknown'),
            item.get('category'),
            json.dumps(item.get('features', [])) if item.get('features') else None,
            item.get('image_url')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error saving item error: {str(e)}")

def update_upload_progress(upload_id, processed_count, total_count):
    """Update upload progress in database"""
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        # Get manifest_id for this upload
        cursor.execute("SELECT manifest_id FROM uploads WHERE id = %s", (upload_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return
        
        manifest_id = result[0]
        
        # Count actual processed items from database (to handle out-of-order processing)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_items
            FROM items 
            WHERE manifest_id = %s
        """, (manifest_id,))
        result = cursor.fetchone()
        total_items_in_db = result[0]
        processed_items_in_db = result[1]
        
        # Calculate status - complete when all items in DB are processed
        # (not when processed >= total_count, because duplicates reduce total_items_in_db)
        status = 'processing'
        if processed_items_in_db >= total_items_in_db and total_items_in_db > 0:
            status = 'completed'
            
            # Update manifest summary when completing
            cursor.execute("""
                UPDATE manifests 
                SET total_msrp = (
                        SELECT COALESCE(SUM(msrp * quantity), 0) 
                        FROM items WHERE manifest_id = %s
                    ),
                    projected_revenue = (
                        SELECT COALESCE(SUM(estimated_sale_price * quantity), 0) 
                        FROM items WHERE manifest_id = %s
                    ),
                    profit_margin = (
                        SELECT 
                            CASE 
                                WHEN SUM(estimated_sale_price * quantity) > 0 
                                THEN (SUM(estimated_sale_price * quantity) - (SUM(estimated_sale_price * quantity) * 0.30)) / (SUM(estimated_sale_price * quantity) * 0.30)
                                ELSE 0 
                            END
                        FROM items 
                        WHERE manifest_id = %s
                    )
                WHERE id = %s
            """, (manifest_id, manifest_id, manifest_id, manifest_id))
            logger.info(f"Updated manifest summary for completed upload")
        
        # Update upload record with actual count from database
        cursor.execute("""
            UPDATE uploads 
            SET processed_items = %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (processed_items_in_db, status, upload_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Updated progress: {processed_items_in_db}/{total_items_in_db} ({status})")
        
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")

