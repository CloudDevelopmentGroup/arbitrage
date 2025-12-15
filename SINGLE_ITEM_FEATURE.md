# Single Item Checker Feature

This document describes the new Single Item Checker feature that allows users to analyze individual items without uploading a full CSV manifest.

## Overview

The Single Item Checker provides a quick way to evaluate individual liquidation items for resale potential. Users can enter item details manually and receive instant AI-powered analysis.

## Architecture

### Backend Components

#### 1. Lambda Function: `item_checker.py`
- **Location**: `/lambda/item_checker.py`
- **Purpose**: Analyzes individual items without database persistence
- **Handler**: `lambda_handler`
- **Timeout**: 30 seconds
- **Memory**: 512MB

**Key Features**:
- Accepts item details via POST request
- Uses existing AI analysis functions from `csv_processor_async.py`
- Returns analysis results without storing to database
- Calculates profit margins, ROI, and purchase recommendations
- Supports quantity calculations for bulk purchases

**Request Format**:
```json
{
  "item_number": "SKU123",
  "title": "Industrial Compressor",
  "msrp": 599.99,
  "quantity": 5,
  "notes": "New in box"
}
```

**Response Format**:
```json
{
  "item": {
    "item_number": "SKU123",
    "title": "Industrial Compressor",
    "msrp": 599.99,
    "quantity": 5,
    "notes": "New in box"
  },
  "analysis": {
    "estimatedSalePrice": 269.99,
    "purchasePrice": 80.99,
    "profitPerItem": 189.00,
    "demand": "High",
    "salesTime": "2-4 months",
    "reasoning": "High demand industrial equipment...",
    "profitMargin": 0.15
  },
  "summary": {
    "totalInvestment": 404.95,
    "totalRevenue": 1349.95,
    "totalProfit": 945.00,
    "roi": 233.4,
    "quantity": 5
  }
}
```

#### 2. API Endpoint: `/prod/check-item`
- **Method**: POST
- **Authentication**: None (public endpoint)
- **CORS**: Enabled
- **Integration**: AWS Lambda Proxy

### Frontend Components

#### 1. Component: `SingleItemChecker.js`
- **Location**: `/frontend/src/components/SingleItemChecker.js`
- **Purpose**: User interface for single item analysis

**Features**:
- Clean, intuitive form for item details
- Real-time validation
- Loading states with progress indicators
- Detailed analysis results display
- Quantity-based calculations
- Quick reset and re-check functionality

**Form Fields**:
- Item Number (optional)
- Title (required)
- MSRP (required, must be > 0)
- Quantity (default: 1)
- Notes (optional)

**Results Display**:
- Item information summary
- Estimated sale price
- Suggested purchase price (30% of sale price)
- Profit per item
- Demand level (color-coded)
- Estimated sales time
- AI reasoning
- Total summary (when quantity > 1)
  - Total investment
  - Total revenue
  - Total profit
  - ROI percentage

#### 2. Updated App Component
- **Location**: `/frontend/src/App.js`
- **Changes**: Added mode switching between manifest and single-item

**New Features**:
- Mode selector in header
- "Check Single Item" button
- Seamless navigation between modes
- State management for both modes

## Deployment

### Prerequisites
- AWS CLI configured
- Terraform installed
- Lambda dependencies installed in `/lambda` directory

### Steps

1. **Package Lambda Function**
```bash
cd lambda
zip -r item_checker.zip item_checker.py csv_processor_async.py psycopg2/ boto3/ requests/ urllib3/ certifi/
```

2. **Deploy Infrastructure**
```bash
cd infrastructure
terraform init
terraform apply
```

Or use the deployment script:
```bash
./deploy_item_checker.sh
```

3. **Deploy API Gateway Changes**
```bash
aws apigateway create-deployment \
  --rest-api-id YOUR_API_ID \
  --stage-name prod
```

4. **Build and Deploy Frontend**
```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-frontend-bucket/
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Usage

### Frontend Usage

1. Navigate to the Arbitrage Analyzer app
2. Click "Check Single Item" button in the header
3. Fill in item details:
   - Enter item title (required)
   - Enter MSRP (required)
   - Optionally add item number, quantity, and notes
4. Click "Analyze Item"
5. Review the analysis results
6. Click "Check Another Item" to analyze more items
7. Click "Analyze Full Manifest" to switch to CSV upload mode

### API Usage

**Endpoint**: `POST https://YOUR_API_URL/prod/check-item`

**Example cURL**:
```bash
curl -X POST https://YOUR_API_URL/prod/check-item \
  -H "Content-Type: application/json" \
  -d '{
    "item_number": "ABC123",
    "title": "Milwaukee Power Drill Kit",
    "msrp": 199.99,
    "quantity": 3,
    "notes": "New, sealed boxes"
  }'
```

## Pricing Model

The analysis uses a liquidation purchase model:
- **Purchase Price**: 30% of estimated sale price
- **Profit**: Sale price - Purchase price
- **ROI**: (Profit / Purchase price) × 100

This model assumes buying at approximately 15-30% of MSRP through liquidation channels.

## AI Analysis

The feature leverages the same AI analysis engine as the CSV manifest processor:

1. **Primary**: OpenAI GPT-4 API (if configured)
   - Contextual analysis
   - Market research
   - Demand assessment
   - Realistic pricing

2. **Fallback**: Mock analysis
   - Rule-based pricing
   - Category-based demand
   - Predictable results

## Error Handling

- **Invalid Input**: Returns 400 with error message
- **Missing Required Fields**: Client-side validation + 400 error
- **AI API Failure**: Automatic fallback to mock analysis
- **Server Error**: Returns 500 with error details

## Performance

- **Average Response Time**: 2-5 seconds (with AI)
- **Fallback Response Time**: < 500ms (mock analysis)
- **Concurrent Requests**: Supported via Lambda scaling
- **Cost**: ~$0.01 per analysis (AI API costs)

## Future Enhancements

1. **Database Integration** (optional)
   - Save individual checks to history
   - Compare items across checks
   - Track price trends

2. **Marketplace Integration**
   - Real-time eBay/Amazon pricing
   - Current market availability
   - Competitive analysis

3. **Batch Single Items**
   - Add multiple items to a list
   - Compare items side-by-side
   - Export results to CSV

4. **Image Analysis**
   - Upload item photos
   - Visual condition assessment
   - Automatic product identification

5. **Price Alerts**
   - Set target margins
   - Get notifications for good deals
   - Market price monitoring

## Testing

### Manual Testing
1. Test with various MSRP values ($10, $100, $1000+)
2. Test with different quantities
3. Test with missing optional fields
4. Test with invalid inputs
5. Verify calculations are correct

### Integration Testing
```bash
# Test the API endpoint
curl -X POST https://YOUR_API_URL/prod/check-item \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Item","msrp":99.99}'
```

## Troubleshooting

### Common Issues

1. **"Invalid JSON body" error**
   - Check request Content-Type header
   - Verify JSON is valid
   - Ensure body is not base64 encoded unexpectedly

2. **AI analysis always falls back to mock**
   - Check OpenAI API key in environment variables
   - Verify Lambda has internet access
   - Check CloudWatch logs for API errors

3. **CORS errors**
   - Verify OPTIONS method is configured
   - Check CORS headers in Lambda response
   - Clear browser cache

4. **Deployment fails**
   - Ensure all dependencies are in the zip file
   - Check Terraform state
   - Verify AWS credentials

## Support

For issues or questions:
- Check CloudWatch logs: `/aws/lambda/arbitrage-item-checker`
- Review API Gateway logs
- Check frontend console for errors
- Verify environment variables are set correctly

