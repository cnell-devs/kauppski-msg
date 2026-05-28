resource "aws_apigatewayv2_api" "ws" {
  name                       = "${var.app_name}-${var.env}-messenger-ws"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

locals {
  routes = {
    "$connect"         = "connect"
    "$disconnect"      = "disconnect"
    "sendMessage"      = "send_message"
    "getMessages"      = "get_messages"
    "listConversations" = "list_conversations"
    "markRead"         = "mark_read"
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each = local.routes

  api_id                    = aws_apigatewayv2_api.ws.id
  integration_type          = "AWS_PROXY"
  integration_uri           = aws_lambda_function.messenger[each.value].invoke_arn
  content_handling_strategy = "CONVERT_TO_TEXT"
  passthrough_behavior      = "WHEN_NO_MATCH"
}

resource "aws_apigatewayv2_route" "routes" {
  for_each = local.routes

  api_id    = aws_apigatewayv2_api.ws.id
  route_key = each.key
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_stage" "prod" {
  count  = var.env == "prod" ? 1 : 0
  api_id = aws_apigatewayv2_api.ws.id
  name   = "prod"
  auto_deploy = true

  default_route_settings {
    logging_level            = "INFO"
    data_trace_enabled       = true
    throttling_burst_limit   = 100
    throttling_rate_limit    = 50
  }
}

resource "aws_apigatewayv2_stage" "dev" {
  count  = var.env == "dev" ? 1 : 0
  api_id = aws_apigatewayv2_api.ws.id
  name   = "dev"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }
}

# ── HTTP API ──────────────────────────────────────────────────────────────────

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.app_name}-${var.env}-messenger-http"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "http_get_messages" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.http_get_messages.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_messages" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /conversations/{conversationId}/messages"
  target    = "integrations/${aws_apigatewayv2_integration.http_get_messages.id}"
}

resource "aws_apigatewayv2_integration" "http_list_conversations" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.http_list_conversations.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "list_conversations" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /conversations"
  target    = "integrations/${aws_apigatewayv2_integration.http_list_conversations.id}"
}

resource "aws_apigatewayv2_stage" "http" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = var.env
  auto_deploy = true
}
