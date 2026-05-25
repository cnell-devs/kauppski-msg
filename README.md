# kauppski-msg

Real-time WebSocket messaging backend for the kauppski platform. Built on AWS Lambda + API Gateway v2 with DynamoDB for persistence and Supabase JWT authentication.

## Architecture

WebSocket connections are managed via AWS API Gateway v2. Each route maps to a dedicated Lambda function. DynamoDB stores connections, messages, and conversations.

```
Client (WSS) → API Gateway v2 → Lambda Functions → DynamoDB
                                       ↑
                               Supabase JWKS (auth)
```

**AWS Resources:**
- 6 Lambda functions (Python 3.12)
- API Gateway v2 WebSocket API
- 3 DynamoDB tables: `connections`, `messages`, `conversations`
- IAM role with scoped DynamoDB + APIGW ManageConnections permissions

## WebSocket Routes

| Route | Handler | Description |
|---|---|---|
| `$connect` | `connect` | Authenticate token, register connection |
| `$disconnect` | `disconnect` | Remove connection record |
| `sendMessage` | `send_message` | Send message, push to recipient if online |
| `getMessages` | `get_messages` | Paginated message history for a conversation |
| `listConversations` | `list_conversations` | All conversations for authenticated user |
| `markRead` | `mark_read` | Reset unread count for a conversation |

## Project Structure

```
kauppski-msg/
├── lambdas/
│   ├── connect/
│   ├── disconnect/
│   ├── send_message/
│   ├── get_messages/
│   ├── list_conversations/
│   ├── mark_read/
│   ├── shared/           # auth.py, dynamo.py, ws.py
│   └── requirements.txt
├── models/               # Python dataclasses (conversations, chats, connections)
├── terraform/            # All infrastructure as code
└── .github/workflows/
    ├── deploy.yml        # Plan + apply pipeline
    └── bootstrap.yml     # Terraform state infrastructure
```

## Authentication

Connections are authenticated via Supabase RS256 JWTs. The `connect` route validates the token against the Supabase JWKS endpoint (cached for 1 hour) before registering the connection. All other routes require an active authenticated connection.

## Data Design

- **Conversation IDs** are `userA#userB` with sorted user IDs — ensures the same conversation ID regardless of who initiates.
- **Message sort keys** are `createdAt#messageId` — prevents collisions and maintains chronological order.
- **Connection records** have a 24-hour TTL for automatic cleanup of stale connections.
- **Unread counts** are incremented on send and reset (not decremented) on `markRead`.

## Deployment

Deploys automatically via GitHub Actions on push to `develop` (dev) or `main` (prod).

**Pipeline:**
1. **bootstrap** — creates S3 state bucket and DynamoDB lock table if missing
2. **plan** — builds Lambda zips, runs `terraform plan`, uploads plan artifact
3. **apply** — downloads plan artifact, runs `terraform apply`

AWS credentials use OIDC federation — no hardcoded secrets.

**Required GitHub Secrets:**

| Secret | Description |
|---|---|
| `AWS_ROLE_ARN` | IAM role ARN for OIDC federation |
| `SUPABASE_URL` | Supabase project URL (used for JWKS endpoint) |

## Environments

| Environment | Branch | Throttle |
|---|---|---|
| `dev` | `develop` | 5 req/s |
| `prod` | `main` | 50 req/s |

Separate Terraform state per environment. DynamoDB uses pay-per-request billing.

## Local Development

**Prerequisites:** Python 3.12, Terraform, AWS CLI, configured AWS credentials.

```bash
# Install Lambda dependencies
pip install -r lambdas/requirements.txt

# Plan infrastructure changes
cd terraform
terraform init
terraform plan -var="supabase_url=<your-supabase-url>"
```

## Frontend Integration

The WebSocket URL is output by Terraform as `wss_url`. Set it in your frontend:

```
NEXT_PUBLIC_WS_URL=wss://<api-id>.execute-api.<region>.amazonaws.com/<env>
```

Connect with a valid Supabase JWT as the `token` query parameter:

```
wss://<endpoint>?token=<supabase-jwt>
```
