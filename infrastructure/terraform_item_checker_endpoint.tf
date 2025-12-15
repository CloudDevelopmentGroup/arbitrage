# API Gateway /check-item endpoint configuration

# Lambda Function for Item Checker
resource "aws_lambda_function" "item_checker" {
  filename         = "${path.module}/../lambda/item_checker.zip"
  function_name    = "arbitrage-item-checker"
  role            = aws_iam_role.lambda_role.arn
  handler         = "item_checker.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../lambda/item_checker.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      # Database config is optional for item checker (not used)
      DB_HOST     = aws_db_instance.arbitrage_db.endpoint
      DB_NAME     = aws_db_instance.arbitrage_db.db_name
      DB_USER     = aws_db_instance.arbitrage_db.username
      DB_PASSWORD = aws_db_instance.arbitrage_db.password
      OPENAI_API_KEY = data.aws_secretsmanager_secret.api_keys.arn
    }
  }

  # No VPC config - item checker doesn't need database access

  tags = {
    Name = "arbitrage-item-checker"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "item_checker_logs" {
  name              = "/aws/lambda/arbitrage-item-checker"
  retention_in_days = 7
}

# API Gateway Resource
resource "aws_api_gateway_resource" "check_item" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  parent_id   = aws_api_gateway_rest_api.arbitrage_api.root_resource_id
  path_part   = "check-item"
}

# POST method for check-item endpoint
resource "aws_api_gateway_method" "check_item_post" {
  rest_api_id   = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id   = aws_api_gateway_resource.check_item.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "check_item_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id             = aws_api_gateway_resource.check_item.id
  http_method             = aws_api_gateway_method.check_item_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.item_checker.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "item_checker_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.item_checker.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.arbitrage_api.execution_arn}/*/*"
}

# OPTIONS method for CORS preflight
resource "aws_api_gateway_method" "check_item_options" {
  rest_api_id   = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id   = aws_api_gateway_resource.check_item.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "check_item_options" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.check_item.id
  http_method = aws_api_gateway_method.check_item_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "check_item_options_200" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.check_item.id
  http_method = aws_api_gateway_method.check_item_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "check_item_options" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.check_item.id
  http_method = aws_api_gateway_method.check_item_options.http_method
  status_code = aws_api_gateway_method_response.check_item_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

