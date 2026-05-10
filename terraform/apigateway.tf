resource "aws_apigatewayv2_api" "ws" {
  name                       = "${var.app_name}-messenger-ws"
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
  api_id      = aws_apigatewayv2_api.ws.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    logging_level            = "INFO"
    data_trace_enabled       = true
    throttling_burst_limit   = 100
    throttling_rate_limit    = 50
  }
}
