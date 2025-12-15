# API Gateway DELETE /upload/{upload_id} endpoint configuration

resource "aws_api_gateway_resource" "upload_id" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  parent_id   = aws_api_gateway_resource.upload.id
  path_part   = "{upload_id}"
}

# DELETE method for upload endpoint
resource "aws_api_gateway_method" "upload_delete" {
  rest_api_id   = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id   = aws_api_gateway_resource.upload_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "upload_delete_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id             = aws_api_gateway_resource.upload_id.id
  http_method             = aws_api_gateway_method.upload_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.csv_processor.invoke_arn
}

# OPTIONS method for CORS preflight
resource "aws_api_gateway_method" "upload_delete_options" {
  rest_api_id   = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id   = aws_api_gateway_resource.upload_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "upload_delete_options" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.upload_id.id
  http_method = aws_api_gateway_method.upload_delete_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "upload_delete_options_200" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.upload_id.id
  http_method = aws_api_gateway_method.upload_delete_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Credentials" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "upload_delete_options_200" {
  rest_api_id = aws_api_gateway_rest_api.arbitrage_api.id
  resource_id = aws_api_gateway_resource.upload_id.id
  http_method = aws_api_gateway_method.upload_delete_options.http_method
  status_code = aws_api_gateway_method_response.upload_delete_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent,X-Amz-Source-Arn,X-Amz-Trace-Id'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Credentials" = "'false'"
  }
}

