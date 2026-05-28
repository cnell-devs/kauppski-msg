import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from datetime import datetime, timezone
from uuid import uuid4

from boto3.dynamodb.conditions import Key
from shared.dynamo import (
    connections_table,
    messages_table,
    conversations_table,
    get_user_id_by_connection,
    get_connection_id_by_user,
)
from shared.ws import post_to_connection, reply


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body") or "{}")

    recipient_id = body.get("recipientId")
    item_id = body.get("itemId")
    content = body.get("content", "").strip()

    if not recipient_id or not item_id or not content:
        return {"statusCode": 400, "body": "recipientId, itemId and content required"}

    sender_id = get_user_id_by_connection(connection_id)
    if not sender_id:
        return {"statusCode": 403, "body": "Unknown connection"}

    now = datetime.now(timezone.utc).isoformat()
    message_id = str(uuid4())
    conversation_id = "#".join(sorted([sender_id, recipient_id]) + [item_id])
    sk = f"{now}#{message_id}"

    # Persist message
    messages_table().put_item(
        Item={
            "conversationId": conversation_id,
            "sk": sk,
            "senderId": sender_id,
            "content": content,
            "createdAt": now,
            "messageId": message_id,
        }
    )

    # Upsert conversation record for sender (reset unread)
    conversations_table().update_item(
        Key={"userId": sender_id, "conversationId": conversation_id},
        UpdateExpression="SET otherUserId = :other, itemId = :item, updatedAt = :ts, lastMessage = :msg",
        ExpressionAttributeValues={
            ":other": recipient_id,
            ":item": item_id,
            ":ts": now,
            ":msg": content[:100],
        },
    )

    # Upsert conversation record for recipient (increment unread)
    conversations_table().update_item(
        Key={"userId": recipient_id, "conversationId": conversation_id},
        UpdateExpression=(
            "SET otherUserId = :other, itemId = :item, updatedAt = :ts, lastMessage = :msg "
            "ADD unreadCount :inc"
        ),
        ExpressionAttributeValues={
            ":other": sender_id,
            ":item": item_id,
            ":ts": now,
            ":msg": content[:100],
            ":inc": 1,
        },
    )

    message_payload = {
        "conversationId": conversation_id,
        "messageId": message_id,
        "senderId": sender_id,
        "content": content,
        "createdAt": now,
    }

    # Echo back to sender
    reply(connection_id, "messageSent", message_payload)

    # Deliver to recipient if online
    recipient_conn = get_connection_id_by_user(recipient_id)
    if recipient_conn:
        delivered = post_to_connection(recipient_conn, {"action": "newMessage", "data": message_payload})
        if not delivered:
            connections_table().delete_item(Key={"connectionId": recipient_conn})

    return {"statusCode": 200, "body": "OK"}
