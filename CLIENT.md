# Client Integration Guide

Everything a frontend needs to build a messaging UI on top of this WebSocket backend.

## Connection

```
wss://<api-id>.execute-api.us-east-1.amazonaws.com/<env>?token=<supabase-jwt>
```

- `env` is `dev` or `prod`.
- `token` is the Supabase **access token** (`session.access_token`) for the signed-in user.
- The token's `sub` claim is treated as the user ID. All messages this user sends or receives reference this ID.

### Lifecycle

| Event | What happens |
|---|---|
| Connect with valid token | Server stores `{connectionId, userId}` with a 24h TTL. |
| Connect with missing token | Server returns `401`; socket closes immediately. |
| Connect with invalid/expired token | Server returns `403`; socket closes immediately. |
| Disconnect (clean or dropped) | Server removes the connection record. |

The JWT is validated against the Supabase JWKS endpoint and supports both `RS256` and `ES256` signatures.

### Reconnecting

- Supabase tokens expire in ~1 hour. Refresh proactively (`supabase.auth.onAuthStateChange`) and reconnect with the new token before expiry.
- On any unexpected close, reconnect with exponential backoff (1s → 2s → 4s → max 30s) and re-fetch initial state via `listConversations`.

### Open race condition

The browser's `WebSocket` is only usable after `onopen` fires. Sends called earlier throw `INVALID_STATE_ERR`. Wrap the socket in a class that queues outgoing messages until `onopen`, then flushes — and treat the connection as "not actually ready" until `onopen` has fired *and* `onclose` hasn't fired in the immediate next tick (an invalid token closes the socket right after open).

## Message Envelope

**Outgoing (client → server)** — a JSON object with an `action` field plus action-specific fields at the top level:

```json
{"action": "sendMessage", "recipientId": "...", "itemId": "...", "content": "..."}
```

**Incoming (server → client)** — always a wrapped envelope:

```json
{"action": "<eventName>", "data": { ... }}
```

Switch on `action` to route to your UI handler.

## Conversations are item-scoped

Every conversation is tied to a specific item from the marketplace. The same two users discussing two different items have two **separate** conversations.

A conversation ID is the two participants' user UUIDs **sorted**, followed by the item UUID, joined by `#`:

```ts
const conversationId = [...[me, them].sort(), itemId].join("#");
// "<userA-sub>#<userB-sub>#<itemId>"
```

You never create conversations explicitly — they exist as soon as the first message is sent. Always compute the ID this way; don't try to remember it.

## Actions

### `sendMessage` — send a message about an item

Request:
```json
{"action": "sendMessage", "recipientId": "<uuid>", "itemId": "<uuid>", "content": "hello"}
```

All three fields are required. `itemId` ties the message to a specific item.

Responses:
- Echo to sender: `{"action": "messageSent", "data": <Message>}`
- Push to recipient (only if they're connected): `{"action": "newMessage", "data": <Message>}`

Offline recipients receive nothing in real time — they'll see the message on their next `listConversations` / `getMessages` call.

### `listConversations` — load the conversation list

Request:
```json
{"action": "listConversations"}
```

Response:
```json
{"action": "conversations", "data": {"items": [<Conversation>, ...]}}
```

Conversations are returned newest-first (sorted by `updatedAt`). Each conversation includes its `itemId` so the UI can render an item preview.

### `getMessages` — load message history for a conversation

Request:
```json
{"action": "getMessages", "conversationId": "<userA>#<userB>#<itemId>", "lastKey": <opaque>?}
```

- Returns 50 messages at a time, oldest-first.
- For pagination, pass the previous response's `nextKey` as `lastKey`. When `nextKey` is absent/null, you've reached the end.
- The caller must be a participant; otherwise the request is rejected with 403.

Response:
```json
{"action": "messages", "data": {"conversationId": "...", "items": [<Message>, ...], "nextKey": <opaque>|null}}
```

### `markRead` — clear unread count

Request:
```json
{"action": "markRead", "conversationId": "<userA>#<userB>#<itemId>"}
```

No response payload. The next `listConversations` will show `unreadCount: 0` for that conversation.

## Data Shapes

### `Message`

```ts
{
  conversationId: string  // "<userA-sub>#<userB-sub>#<itemId>"
  messageId: string       // UUID
  senderId: string        // Supabase user UUID
  content: string
  createdAt: string       // ISO-8601 UTC, e.g. "2026-05-28T02:34:00+00:00"
}
```

`itemId` is not repeated on each message — parse it from the third segment of `conversationId` if you need it: `conversationId.split('#')[2]`.

### `Conversation`

```ts
{
  userId: string          // the viewing user (you)
  conversationId: string  // "<userA-sub>#<userB-sub>#<itemId>"
  otherUserId: string     // the participant who isn't you
  itemId: string          // the item this conversation is about
  updatedAt: string       // ISO-8601 UTC; timestamp of the last message
  lastMessage: string     // first 100 chars of the last message content
  unreadCount: number     // 0 if you've called markRead since the last incoming msg
}
```

The conversation record does **not** include item details (title, photos, etc.) — fetch those from the kauppski items API using `itemId`.

## UI Patterns

### Initial load
1. Authenticate with Supabase, grab `session.access_token`.
2. Open WS with the token in the query string.
3. Wait for `onopen` (and ensure the socket doesn't immediately close).
4. Send `{"action": "listConversations"}`.
5. For each returned conversation, fetch the item (`GET /items/:itemId` on the kauppski API) for thumbnail/title/etc. Cache by `itemId`.
6. Render the conversation list.

### Starting a conversation from an item page
1. From the item page, user clicks "Message seller".
2. Compute the conversation ID locally: `[me, item.owner_id].sort().join("#") + "#" + item.id`.
3. Open the chat view. It will be empty until the first `sendMessage` succeeds.
4. The first send creates the conversation row on both sides.

### Opening an existing conversation
1. Take `conversationId` from the conversation list.
2. Send `{"action": "getMessages", "conversationId"}`.
3. Append received `messages.items` (oldest-first) to the view.
4. Send `{"action": "markRead", "conversationId"}` once messages are visible.

### Sending a message
1. Send `{"action": "sendMessage", "recipientId", "itemId", "content"}`.
2. Optimistically render your own message (use a temporary ID).
3. When `messageSent` comes back, swap your temp ID for the real `messageId`.

### Receiving a message
1. On `newMessage`, append to the open conversation if it matches; otherwise bump the conversation's `lastMessage`/`updatedAt`/`unreadCount` in your local list.
2. If the user is actively viewing the conversation, immediately send `markRead`.

### Pagination (scrollback)
1. When the user scrolls to the top, send `getMessages` with `lastKey` set to the previous response's `nextKey`.
2. Prepend the returned items.
3. Stop when `nextKey` is null.

## Errors

WebSocket-level errors come back outside the envelope, typically as:

```json
{"message": "Internal server error", "connectionId": "...", "requestId": "..."}
```

These mean a Lambda failed. The connection stays open — the client should surface a toast and continue. Application-level rejections (missing fields, not a participant, etc.) currently return HTTP-style status codes via the WebSocket response that the client receives as a plain message; don't rely on these as a stable contract yet.

## Limits & Gotchas

- **1:1 only.** There's no group chat schema.
- **Item-scoped only.** All conversations require an `itemId`. There's no "general DM" path.
- **No typing indicators, read receipts, or presence.** Add via new actions if needed.
- **No message edit/delete.** Messages are immutable once written.
- **`lastMessage` is truncated** to 100 chars on the conversation record. The full message lives in the `messages` table; fetch via `getMessages`.
- **No push notifications** for offline recipients — they'll see the message next time they connect.
- **One active connection per user.** The server looks up the recipient by `userId` and pushes to that connection; if the user has multiple tabs open, only the most-recent one receives real-time pushes.
- **Token refresh requires reconnect.** There's no in-band token rotation.
- **Item details aren't denormalized.** The conversation row only stores `itemId`. UI must fetch item title/photos from the kauppski items API.
