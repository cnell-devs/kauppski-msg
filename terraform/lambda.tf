locals {
  lambda_src_root = "${path.module}/../lambdas"

  functions = {
    connect            = "connect"
    disconnect         = "disconnect"
    send_message       = "send_message"
    get_messages       = "get_messages"
    list_conversations = "list_conversations"
    mark_read          = "mark_read"
  }
}

resource "aws_lambda_layer_version" "deps" {
  layer_name          = "${var.app_name}-${var.env}-messenger-deps"
  filename            = "${path.module}/.lambda_zips/layer.zip"
  source_code_hash    = filebase64sha256("${path.module}/.lambda_zips/layer.zip")
  compatible_runtimes = ["python3.12"]
}

resource "aws_lambda_function" "messenger" {
  for_each = local.functions

  function_name    = "${var.app_name}-${var.env}-messenger-${each.key}"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "${each.value}/handler.handler"
  filename         = "${path.module}/.lambda_zips/${each.key}.zip"
  source_code_hash = filebase64sha256("${path.module}/.lambda_zips/${each.key}.zip")
  layers           = [aws_lambda_layer_version.deps.arn]
  timeout          = 10

  environment {
    variables = {
      CONNECTIONS_TABLE   = aws_dynamodb_table.connections.name
      MESSAGES_TABLE      = aws_dynamodb_table.messages.name
      CONVERSATIONS_TABLE = aws_dynamodb_table.conversations.name
      SUPABASE_URL        = var.supabase_url
      APIGW_ENDPOINT      = "https://${aws_apigatewayv2_api.ws.id}.execute-api.us-east-1.amazonaws.com/${var.env}"
    }
  }

  depends_on = [aws_apigatewayv2_api.ws]
}

# Allow API Gateway to invoke each Lambda
resource "aws_lambda_permission" "apigw" {
  for_each = local.functions

  statement_id  = "AllowAPIGW-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.messenger[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ws.execution_arn}/*/*"
}
