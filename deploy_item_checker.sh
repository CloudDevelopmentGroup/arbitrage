#!/bin/bash

# Deploy Item Checker Lambda Function
# This script packages and deploys the item checker Lambda function

set -e

echo "=== Deploying Item Checker Lambda Function ==="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd lambda

echo -e "${YELLOW}Step 1: Cleaning up old package...${NC}"
rm -f item_checker.zip

echo -e "${YELLOW}Step 2: Creating deployment package...${NC}"
zip -r item_checker.zip item_checker.py csv_processor_async.py

echo -e "${YELLOW}Step 3: Adding dependencies...${NC}"
# Add psycopg2 and other dependencies if they exist
if [ -d "psycopg2" ]; then
    zip -r item_checker.zip psycopg2/
fi
if [ -d "boto3" ]; then
    zip -r item_checker.zip boto3/
fi
if [ -d "botocore" ]; then
    zip -r item_checker.zip botocore/
fi
if [ -d "requests" ]; then
    zip -r item_checker.zip requests/
fi
if [ -d "urllib3" ]; then
    zip -r item_checker.zip urllib3/
fi
if [ -d "certifi" ]; then
    zip -r item_checker.zip certifi/
fi
if [ -d "charset_normalizer" ]; then
    zip -r item_checker.zip charset_normalizer/
fi
if [ -d "idna" ]; then
    zip -r item_checker.zip idna/
fi
if [ -d "dateutil" ]; then
    zip -r item_checker.zip dateutil/
fi

echo -e "${GREEN}✓ Package created: item_checker.zip${NC}"

cd ..

echo -e "${YELLOW}Step 4: Deploying with Terraform...${NC}"
cd infrastructure

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
fi

# Apply only the item checker resources
echo "Applying Terraform configuration..."
terraform apply -target=aws_lambda_function.item_checker \
                -target=aws_cloudwatch_log_group.item_checker_logs \
                -target=aws_api_gateway_resource.check_item \
                -target=aws_api_gateway_method.check_item_post \
                -target=aws_api_gateway_integration.check_item_lambda \
                -target=aws_lambda_permission.item_checker_api_gateway \
                -target=aws_api_gateway_method.check_item_options \
                -target=aws_api_gateway_integration.check_item_options \
                -target=aws_api_gateway_method_response.check_item_options_200 \
                -target=aws_api_gateway_integration_response.check_item_options

cd ..

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "The item checker endpoint is now available at:"
echo "POST https://YOUR_API_GATEWAY_URL/prod/check-item"
echo ""
echo "You may need to deploy the API Gateway changes manually:"
echo "aws apigateway create-deployment --rest-api-id YOUR_API_ID --stage-name prod"

