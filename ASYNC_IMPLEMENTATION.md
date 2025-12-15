# Async Processing Implementation Plan

## Overview
Move from synchronous to asynchronous processing to handle unlimited items without timeout.

## Architecture Flow
```
1. User uploads CSV → csv_uploader Lambda
2. csv_uploader:
   - Parses CSV
   - Creates upload record (status='processing')
   - Sends each item to SQS queue
   - Returns immediately with upload_id
3. Frontend receives upload_id
4. Frontend polls /status/{upload_id} every 2 seconds
5. item_processor Lambda (triggered by SQS):
   - Processes each item with AI
   - Saves to database
   - Updates progress count
6. When all items done, status='completed'
7. Frontend shows results
```

## Implementation Steps

### 1. Database Schema ✅
- Add `status`, `processed_items`, `error_message` to uploads table
- Add unique constraint on items(manifest_id, item_number)

### 2. SQS Queue ✅ (added to Terraform)
- Main queue: arbitrage-item-analysis-queue
- Dead letter queue for failures

### 3. Background Processor Lambda ✅
- Created item_processor.py
- Processes one item at a time from queue
- Updates database with results

### 4. Modify csv_processor 🔄 (NEXT)
- Parse CSV
- Queue all items to SQS
- Return upload_id immediately
- DON'T process items inline

### 5. Add Status Endpoint 🔄
- GET /status/{upload_id}
- Returns: {status, processed_items, total_items, results (if completed)}

### 6. Update Frontend 🔄
- Show "Processing..." after upload
- Poll status endpoint
- Show progress bar
- Display results when complete

## Key Benefits
- No timeouts (can process unlimited items)
- User sees real-time progress
- Can close browser and come back
- Failed items don't block others
- Scalable (SQS auto-scales)

## Timeline
- Terraform + Schema: 30 min ✅
- Backend changes: 1 hour 🔄
- Frontend changes: 30 min
- Testing: 30 min
- Total: ~2.5 hours
