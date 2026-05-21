import {
  to = aws_dynamodb_table.connections
  id = "${var.app_name}-${var.env}-connections"
}

import {
  to = aws_dynamodb_table.messages
  id = "${var.app_name}-${var.env}-messages"
}

import {
  to = aws_dynamodb_table.conversations
  id = "${var.app_name}-${var.env}-conversations"
}

import {
  to = aws_iam_role.lambda_exec
  id = "${var.app_name}-${var.env}-messenger-lambda-role"
}
