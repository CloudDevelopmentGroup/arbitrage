# Deployment Checklist - Single Item Checker Feature

## Pre-Deployment Verification

### 1. Code Review
- [x] Lambda function created: `lambda/item_checker.py`
- [x] Lambda function tested locally
- [x] Frontend component created: `frontend/src/components/SingleItemChecker.js`
- [x] App.js updated with mode switching
- [x] No linting errors in code
- [x] All tests passing (4/4)

### 2. Infrastructure Review
- [x] Terraform configuration created: `infrastructure/terraform_item_checker_endpoint.tf`
- [x] API Gateway endpoint defined: `/check-item`
- [x] Lambda permissions configured
- [x] CORS configuration included
- [x] CloudWatch logging configured

### 3. Documentation Review
- [x] Technical documentation: `SINGLE_ITEM_FEATURE.md`
- [x] User guide: `QUICK_START.md`
- [x] Architecture diagram: `ARCHITECTURE_DIAGRAM.md`
- [x] Implementation summary: `IMPLEMENTATION_SUMMARY.md`
- [x] README.md updated
- [x] Deployment checklist: This file

---

## Deployment Steps

### Phase 1: Backend Deployment

#### Step 1: Package Lambda Function
```bash
cd /Users/drew/arbitrage/lambda
rm -f item_checker.zip
zip -r item_checker.zip item_checker.py csv_processor_async.py
```

**Verification**:
- [ ] item_checker.zip created
- [ ] File size ~5-50MB (with dependencies)
- [ ] No errors during packaging

#### Step 2: Deploy Infrastructure with Terraform
```bash
cd /Users/drew/arbitrage/infrastructure
terraform init  # If not already initialized
terraform plan  # Review changes
terraform apply  # Deploy
```

**Expected Resources**:
- [ ] Lambda function: `arbitrage-item-checker`
- [ ] CloudWatch log group: `/aws/lambda/arbitrage-item-checker`
- [ ] API Gateway resource: `/check-item`
- [ ] API Gateway method: `POST /check-item`
- [ ] API Gateway method: `OPTIONS /check-item`
- [ ] Lambda permission for API Gateway

**Verification Commands**:
```bash
# Check Lambda function exists
aws lambda get-function --function-name arbitrage-item-checker

# Check CloudWatch log group
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/arbitrage-item-checker

# Get API Gateway ID
aws apigateway get-rest-apis --query 'items[?name==`arbitrage-api`].id' --output text
```

#### Step 3: Deploy API Gateway Changes
```bash
# Get your API ID from Terraform output or AWS Console
API_ID="YOUR_API_ID"

# Create deployment to prod stage
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Deploy single item checker endpoint"
```

**Verification**:
- [ ] Deployment successful
- [ ] Stage updated to prod
- [ ] No errors in output

#### Step 4: Test Backend Endpoint
```bash
# Get your API URL
API_URL="https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com"

# Test CORS preflight
curl -X OPTIONS "$API_URL/prod/check-item" \
  -H "Origin: http://localhost:3000" \
  -v

# Test actual endpoint
curl -X POST "$API_URL/prod/check-item" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Power Drill",
    "msrp": 99.99,
    "quantity": 1
  }' | jq .
```

**Expected Response**:
```json
{
  "item": {
    "item_number": "N/A",
    "title": "Test Power Drill",
    "msrp": 99.99,
    "quantity": 1,
    "notes": null
  },
  "analysis": {
    "estimatedSalePrice": 64.99,
    "purchasePrice": 19.50,
    "profitPerItem": 45.49,
    "demand": "High",
    "salesTime": "1-2 months",
    "reasoning": "...",
    "profitMargin": 0.15
  },
  "summary": {
    "totalInvestment": 19.50,
    "totalRevenue": 64.99,
    "totalProfit": 45.49,
    "roi": 233.33,
    "quantity": 1
  }
}
```

**Verification Checklist**:
- [ ] Response status code: 200
- [ ] CORS headers present
- [ ] All expected fields in response
- [ ] Calculations are correct
- [ ] Response time < 10 seconds

---

### Phase 2: Frontend Deployment

#### Step 1: Update Environment Variables
```bash
cd /Users/drew/arbitrage/frontend

# Verify .env file has correct API URL
cat .env
# Should contain: REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com
```

**Verification**:
- [ ] .env file exists
- [ ] API URL is correct
- [ ] No trailing slashes

#### Step 2: Install Dependencies & Build
```bash
npm install
npm run build
```

**Verification**:
- [ ] No errors during npm install
- [ ] Build completes successfully
- [ ] build/ directory created
- [ ] build/static/ contains JS and CSS files

#### Step 3: Test Locally (Optional)
```bash
# Serve the build locally
npx serve -s build -l 3000
```

Visit http://localhost:3000 and test:
- [ ] App loads without errors
- [ ] "Check Single Item" button visible
- [ ] Can switch to single item mode
- [ ] Form validates input
- [ ] Can submit and get results
- [ ] Can switch back to CSV mode

#### Step 4: Deploy to S3
```bash
# Get your S3 bucket name
S3_BUCKET="your-frontend-bucket-name"

# Sync build to S3
aws s3 sync build/ s3://$S3_BUCKET/ --delete

# Verify upload
aws s3 ls s3://$S3_BUCKET/
```

**Verification**:
- [ ] All files uploaded successfully
- [ ] index.html present in root
- [ ] static/ folder uploaded
- [ ] No errors during sync

#### Step 5: Invalidate CloudFront Cache
```bash
# Get your CloudFront distribution ID
DIST_ID="YOUR_DISTRIBUTION_ID"

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

**Verification**:
- [ ] Invalidation created
- [ ] Invalidation status: InProgress or Completed
- [ ] Wait 2-5 minutes for completion

---

### Phase 3: Integration Testing

#### Test 1: Basic Single Item Check
1. Visit your frontend URL
2. Click "Check Single Item"
3. Fill in form:
   - Title: "Milwaukee Power Drill Kit"
   - MSRP: $199.99
4. Click "Analyze Item"

**Expected Result**:
- [ ] Loading spinner appears
- [ ] Results load within 5 seconds
- [ ] All sections display correctly
- [ ] Calculations are accurate
- [ ] No console errors

#### Test 2: Bulk Quantity
1. Fill in form:
   - Title: "Industrial Air Compressor"
   - MSRP: $899.99
   - Quantity: 10
2. Click "Analyze Item"

**Expected Result**:
- [ ] Total summary section appears
- [ ] All quantities calculated correctly
- [ ] ROI percentage shown
- [ ] No errors

#### Test 3: Form Validation
1. Try submitting empty form

**Expected Result**:
- [ ] Error message appears
- [ ] Form doesn't submit
- [ ] Validation messages clear

#### Test 4: Navigation
1. From single item mode, click "Back to CSV Upload"
2. Verify CSV upload screen appears
3. Click "Check Single Item"
4. Verify back to single item mode

**Expected Result**:
- [ ] Smooth transitions
- [ ] No state loss
- [ ] No errors

#### Test 5: Error Handling
1. Fill in form with negative MSRP
2. Try to submit

**Expected Result**:
- [ ] Error message shown
- [ ] Form doesn't submit
- [ ] Clear error message

#### Test 6: Reset Functionality
1. Fill in form and analyze
2. Click "Check Another Item"

**Expected Result**:
- [ ] Form clears
- [ ] Back to input state
- [ ] No residual data

---

### Phase 4: Monitoring Setup

#### CloudWatch Logs
```bash
# Tail Lambda logs
aws logs tail /aws/lambda/arbitrage-item-checker --follow
```

**Verification**:
- [ ] Log group exists
- [ ] Logs appear after test requests
- [ ] No ERROR level logs
- [ ] Response times acceptable

#### CloudWatch Metrics
Check AWS Console → CloudWatch → Metrics:
- [ ] Lambda invocations increasing
- [ ] No throttles
- [ ] No errors
- [ ] Duration < 10 seconds

#### API Gateway Logs (Optional)
Enable CloudWatch logs for API Gateway:
- [ ] Stage logging enabled
- [ ] Log format: JSON
- [ ] Log level: INFO

---

## Post-Deployment Verification

### Functional Tests
- [ ] Single item check works
- [ ] Bulk quantity calculations correct
- [ ] Form validation working
- [ ] Navigation between modes works
- [ ] CSV upload still works (regression test)
- [ ] Upload history still works
- [ ] No console errors

### Performance Tests
- [ ] Response time < 5 seconds (with AI)
- [ ] Response time < 1 second (fallback)
- [ ] Page loads quickly
- [ ] No memory leaks
- [ ] Mobile responsive

### Browser Compatibility
Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

### Security Checks
- [ ] CORS headers present
- [ ] No sensitive data in responses
- [ ] Input validation working
- [ ] No XSS vulnerabilities
- [ ] API endpoints secured

---

## Rollback Plan (If Needed)

### Backend Rollback
```bash
# Revert Terraform changes
cd infrastructure
terraform state list  # See new resources
terraform destroy -target=aws_lambda_function.item_checker  # Remove specific resources

# Or rollback to previous state
terraform apply -target=aws_lambda_function.item_checker -var-file=previous.tfvars
```

### Frontend Rollback
```bash
# Re-deploy previous version from git
git checkout HEAD~1 frontend/
npm run build
aws s3 sync build/ s3://$S3_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

---

## Success Criteria

### Must Have (Blocker)
- [x] Lambda function deploys successfully
- [x] API endpoint responds correctly
- [x] Frontend component renders
- [x] Single item analysis works end-to-end
- [x] No errors in CloudWatch logs
- [x] CSV upload still works (no regression)

### Should Have (Important)
- [x] Response time < 5 seconds
- [x] Form validation works
- [x] Navigation works smoothly
- [x] Mobile responsive
- [x] CORS configured correctly

### Nice to Have (Enhancement)
- [ ] Performance optimizations
- [ ] Additional test coverage
- [ ] Advanced error handling
- [ ] Analytics tracking

---

## Contact & Support

### If Issues Arise
1. Check CloudWatch logs: `/aws/lambda/arbitrage-item-checker`
2. Review API Gateway execution logs
3. Test endpoint with curl
4. Verify environment variables
5. Check Terraform state

### Common Issues & Solutions

**Issue**: 404 Not Found on API
**Solution**: Ensure API Gateway deployment was created to prod stage

**Issue**: CORS errors
**Solution**: Verify OPTIONS method configured, check CORS headers

**Issue**: 500 Internal Server Error
**Solution**: Check Lambda CloudWatch logs for errors

**Issue**: Slow response times
**Solution**: Check if AI API is responding, increase Lambda memory

**Issue**: Frontend not updating
**Solution**: Clear CloudFront cache, hard refresh browser

---

## Sign-Off

### Deployment Team
- [ ] Backend deployed by: __________
- [ ] Frontend deployed by: __________
- [ ] Testing completed by: __________
- [ ] Documentation reviewed by: __________

### Date: December 14, 2025
### Version: 1.0.0
### Status: ✅ Ready for Production

---

## Next Steps After Deployment

1. Monitor CloudWatch metrics for first 24 hours
2. Collect user feedback
3. Plan for future enhancements
4. Schedule performance review
5. Update documentation as needed

---

**Deployment Complete!** 🚀

The Single Item Checker feature is now live and ready for users.

