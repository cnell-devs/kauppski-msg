import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from shared.dynamo import conversations_table, get_user_id_by_connection


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body") or "{}")

    conversation_id = body.get("conversationId")
    if not conversation_id:
        return {"statusCode": 400, "body": "conversationId required"}

    user_id = get_user_id_by_connection(connection_id)
    if not user_id:
        return {"statusCode": 403, "body": "Unknown connection"}

    conversations_table().update_item(
        Key={"userId": user_id, "conversationId": conversation_id},
        UpdateExpression="SET unreadCount = :zero",
        ExpressionAttributeValues={":zero": 0},
    )

    return {"statusCode": 200, "body": "OK"}
