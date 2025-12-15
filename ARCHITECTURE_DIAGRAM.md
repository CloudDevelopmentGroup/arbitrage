# Architecture Diagram - Single Item Checker vs CSV Manifest

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React.js)                            │
│                        Hosted on S3 + CloudFront                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────┐              ┌─────────────────────────┐        │
│  │   App Component    │◄─────────────┤   Mode: 'manifest'      │        │
│  │                    │              │   Mode: 'single-item'   │        │
│  └─────────┬──────────┘              └─────────────────────────┘        │
│            │                                                              │
│            │                                                              │
│   ┌────────┴────────┐                                                    │
│   │                 │                                                    │
│   ▼                 ▼                                                    │
│ ┌──────────────┐  ┌──────────────────┐                                  │
│ │   CSV        │  │  Single Item     │                                  │
│ │   Upload     │  │  Checker         │                                  │
│ │   Component  │  │  Component       │                                  │
│ └──────┬───────┘  └────────┬─────────┘                                  │
│        │                   │                                             │
└────────┼───────────────────┼─────────────────────────────────────────────┘
         │                   │
         │ POST /upload      │ POST /check-item
         │                   │
         ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                                      │
│                    REST API + CORS Enabled                               │
└──────────┬─────────────────────────┬────────────────────────────────────┘
           │                         │
           │                         │
    ┌──────▼──────┐          ┌──────▼──────────┐
    │   Lambda:   │          │    Lambda:      │
    │ csv_uploader│          │  item_checker   │
    └──────┬──────┘          └──────┬──────────┘
           │                        │
           │ Store to S3            │ Direct Analysis
           ▼                        │ (No DB write)
    ┌─────────────┐                 │
    │  S3 Bucket  │                 │
    │  (uploads)  │                 │
    └──────┬──────┘                 │
           │                        │
           │ Trigger SQS            │
           ▼                        │
    ┌─────────────┐                 │
    │  SQS Queue  │                 │
    │  (items)    │                 │
    └──────┬──────┘                 │
           │                        │
           │ Process Items          │
           ▼                        │
    ┌──────────────┐                │
    │   Lambda:    │◄───────────────┘
    │item_processor│
    └──────┬───────┘
           │
           │ Store Results
           ▼
    ┌─────────────────┐
    │   PostgreSQL    │
    │   RDS Database  │
    └─────────────────┘
```

## Single Item Checker Flow (Detailed)

```
┌─────────────┐
│    USER     │
│  Interface  │
└──────┬──────┘
       │
       │ 1. Click "Check Single Item"
       │
       ▼
┌──────────────────────┐
│  SingleItemChecker   │
│     Component        │
├──────────────────────┤
│  Form Fields:        │
│  • Title (required)  │
│  • MSRP (required)   │
│  • Item # (optional) │
│  • Quantity          │
│  • Notes             │
└──────┬───────────────┘
       │
       │ 2. Submit Form
       │    POST /prod/check-item
       │    {
       │      "title": "...",
       │      "msrp": 99.99,
       │      "quantity": 5
       │    }
       │
       ▼
┌─────────────────────────────────────────┐
│        API Gateway                       │
│  • Validates request                     │
│  • Handles CORS                          │
│  • Routes to Lambda                      │
└──────┬──────────────────────────────────┘
       │
       │ 3. Invoke Lambda
       │
       ▼
┌─────────────────────────────────────────┐
│   Lambda: item_checker.py                │
├─────────────────────────────────────────┤
│                                          │
│  Step 1: Validate Input                 │
│  ├─ Check required fields               │
│  ├─ Validate MSRP > 0                   │
│  └─ Validate quantity >= 1              │
│                                          │
│  Step 2: Build Item Object              │
│  └─ Format data for analysis            │
│                                          │
│  Step 3: AI Analysis                    │
│  ├─ Try OpenAI API                      │
│  └─ Fallback to mock if unavailable     │
│                                          │
│  Step 4: Calculate Profitability        │
│  ├─ Estimated sale price (AI)           │
│  ├─ Purchase price (30% of sale)        │
│  ├─ Profit per item                     │
│  └─ Total calculations (× quantity)     │
│                                          │
│  Step 5: Format Response                │
│  └─ Build JSON response                 │
│                                          │
└──────┬──────────────────────────────────┘
       │
       │ 4. Return Results
       │    {
       │      "item": {...},
       │      "analysis": {...},
       │      "summary": {...}
       │    }
       │
       ▼
┌─────────────────────────────────────────┐
│      Frontend Display                    │
├─────────────────────────────────────────┤
│  • Item information                      │
│  • Estimated sale price                  │
│  • Suggested purchase price              │
│  • Profit per item                       │
│  • Demand level (color-coded)            │
│  • Sales time estimate                   │
│  • AI reasoning                          │
│  • Total summary (if qty > 1)            │
└─────────────────────────────────────────┘
```

## CSV Manifest Flow (Existing)

```
┌─────────────┐
│    USER     │
│  Interface  │
└──────┬──────┘
       │
       │ 1. Upload CSV File
       │
       ▼
┌──────────────────────┐
│   CSV Upload         │
│   Component          │
└──────┬───────────────┘
       │
       │ 2. POST /prod/upload
       │
       ▼
┌──────────────────────┐
│  Lambda:             │
│  csv_uploader        │
│                      │
│  • Store to S3       │
│  • Create DB record  │
│  • Return upload_id  │
└──────┬───────────────┘
       │
       │ 3. Store CSV
       │
       ▼
┌──────────────────────┐
│   S3 Bucket          │
│   (CSV files)        │
└──────┬───────────────┘
       │
       │ 4. Trigger async processing
       │
       ▼
┌──────────────────────┐
│  SQS Queue           │
│  (Item processing)   │
└──────┬───────────────┘
       │
       │ 5. Process each item
       │
       ▼
┌──────────────────────┐
│  Lambda:             │
│  item_processor      │
│                      │
│  • AI analysis       │
│  • Calculate profit  │
│  • Update DB         │
└──────┬───────────────┘
       │
       │ 6. Store results
       │
       ▼
┌──────────────────────┐
│  PostgreSQL RDS      │
│                      │
│  • uploads table     │
│  • manifests table   │
│  • items table       │
└──────┬───────────────┘
       │
       │ 7. Frontend polls status
       │    GET /prod/status/{id}
       │
       ▼
┌──────────────────────┐
│  Display Results     │
│  • Full manifest     │
│  • All items         │
│  • Charts/graphs     │
└──────────────────────┘
```

## Key Differences

### Single Item Checker
- ✅ **Fast**: 2-5 seconds total
- ✅ **Simple**: Direct request/response
- ✅ **No persistence**: Results not saved
- ✅ **Lightweight**: Minimal infrastructure
- ✅ **On-demand**: Check anytime, anywhere
- ⚠️ **No history**: Can't review later

### CSV Manifest
- ✅ **Bulk**: Process 50-100+ items
- ✅ **Persistent**: Saves to database
- ✅ **History**: Review anytime
- ✅ **Comprehensive**: Full analysis + charts
- ⚠️ **Slower**: 1-3 minutes for full manifest
- ⚠️ **More complex**: Multi-step process

## Data Flow Comparison

```
SINGLE ITEM:
User → API Gateway → Lambda → AI → Response → User
        (2-5 seconds)

CSV MANIFEST:
User → Upload → S3 → SQS → Lambda → DB → Poll → Display
        (1-3 minutes for full manifest)
```

## Infrastructure Components

### Shared Resources
- API Gateway (REST API)
- Lambda execution role
- VPC & Security groups
- CloudWatch logs
- OpenAI API integration

### Single Item Specific
- `item_checker.py` Lambda
- `/check-item` API endpoint
- No database dependency
- No S3 storage

### CSV Manifest Specific
- `csv_uploader.py` Lambda
- `item_processor.py` Lambda
- `/upload` API endpoint
- S3 bucket for CSVs
- SQS queue for processing
- PostgreSQL RDS database
- `/status/{id}` endpoint
- `/history` endpoint

## Security & CORS

```
┌─────────────────────┐
│  Browser            │
│  (Frontend)         │
└──────┬──────────────┘
       │
       │ 1. OPTIONS request (preflight)
       │
       ▼
┌─────────────────────┐
│  API Gateway        │
│                     │
│  Returns CORS       │
│  headers:           │
│  • Allow-Origin: *  │
│  • Allow-Methods    │
│  • Allow-Headers    │
└──────┬──────────────┘
       │
       │ 2. POST request
       │
       ▼
┌─────────────────────┐
│  Lambda             │
│                     │
│  Includes CORS      │
│  headers in         │
│  response           │
└─────────────────────┘
```

## Cost Breakdown (per request)

### Single Item Check
- API Gateway: $0.0000035
- Lambda execution: $0.0001
- OpenAI API call: $0.01
- **Total: ~$0.01 per check**

### CSV Manifest (50 items)
- API Gateway: $0.0000035
- S3 storage: $0.0001
- Lambda executions: $0.005
- SQS messages: $0.0002
- OpenAI API calls: $0.50
- Database storage: $0.001
- **Total: ~$0.50 per manifest**

## Performance Metrics

```
Single Item Checker:
├─ Cold start: 2-3 seconds
├─ Warm start: 1-2 seconds
├─ AI analysis: 2-4 seconds
└─ Total: 2-5 seconds

CSV Manifest:
├─ Upload: 5-10 seconds
├─ Per item: 3-5 seconds
├─ 50 items: 2-3 minutes
└─ Total: Depends on item count
```

## Scaling Characteristics

### Single Item
- Concurrent Lambda: 1000
- API Gateway: No limit
- Expected load: <100/min
- Auto-scales instantly

### CSV Manifest
- SQS throughput: 3000/sec
- Lambda concurrency: 1000
- Database connections: 100
- Processes items in parallel

---

This architecture provides both quick single-item checks and comprehensive bulk analysis, giving users flexibility based on their needs.

