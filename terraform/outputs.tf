output "wss_url" {
  description = "WebSocket URL — set as NEXT_PUBLIC_WS_URL in frontend/.env.local"
  value       = var.env == "prod" ? aws_apigatewayv2_stage.prod[0].invoke_url : aws_apigatewayv2_stage.dev[0].invoke_url
}

output "connections_table" {
  value = aws_dynamodb_table.connections.name
}

output "messages_table" {
  value = aws_dynamodb_table.messages.name
}

output "conversations_table" {
  value = aws_dynamodb_table.conversations.name
}
