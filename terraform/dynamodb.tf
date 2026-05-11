resource "aws_dynamodb_table" "connections" {
  name         = "${var.app_name}-${var.env}-connections"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "connectionId"

  attribute {
    name = "connectionId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "userId"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "messages" {
  name         = "${var.app_name}-${var.env}-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "conversationId"
  range_key    = "sk"

  attribute {
    name = "conversationId"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }
}

resource "aws_dynamodb_table" "conversations" {
  name         = "${var.app_name}-${var.env}-conversations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "conversationId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "conversationId"
    type = "S"
  }

  attribute {
    name = "updatedAt"
    type = "S"
  }

  global_secondary_index {
    name            = "UserConversationsIndex"
    hash_key        = "userId"
    range_key       = "updatedAt"
    projection_type = "ALL"
  }
}
