data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.app_name}-messenger-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "messenger_access" {
  statement {
    sid    = "DynamoDB"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]
    resources = [
      aws_dynamodb_table.connections.arn,
      "${aws_dynamodb_table.connections.arn}/index/*",
      aws_dynamodb_table.messages.arn,
      aws_dynamodb_table.conversations.arn,
      "${aws_dynamodb_table.conversations.arn}/index/*",
    ]
  }

  statement {
    sid     = "ApiGwManage"
    effect  = "Allow"
    actions = ["execute-api:ManageConnections"]
    resources = [
      "${aws_apigatewayv2_api.ws.execution_arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "messenger_access" {
  name   = "${var.app_name}-messenger-access"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.messenger_access.json
}
