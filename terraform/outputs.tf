output "wss_url" {
  description = "WebSocket URL — set as NEXT_PUBLIC_WS_URL in frontend/.env.local"
  value       = aws_apigatewayv2_stage.prod.invoke_url
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
