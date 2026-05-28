import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from boto3.dynamodb.conditions import Key
from shared.dynamo import messages_table, get_user_id_by_connection
from shared.ws import reply


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body") or "{}")

    conversation_id = body.get("conversationId")
    if not conversation_id:
        return {"statusCode": 400, "body": "conversationId required"}

    user_id = get_user_id_by_connection(connection_id)
    if not user_id:
        return {"statusCode": 403, "body": "Unknown connection"}

    # Caller must be a participant: conversationId is <userA>#<userB>#<itemId>
    parts = conversation_id.split("#")
    if len(parts) != 3 or user_id not in parts[:2]:
        return {"statusCode": 403, "body": "Not a participant"}

    query_kwargs = dict(
        KeyConditionExpression=Key("conversationId").eq(conversation_id),
        ScanIndexForward=True,
        Limit=50,
    )

    last_key = body.get("lastKey")
    if last_key:
        query_kwargs["ExclusiveStartKey"] = last_key

    resp = messages_table().query(**query_kwargs)

    reply(connection_id, "messages", {
        "conversationId": conversation_id,
        "items": resp.get("Items", []),
        "nextKey": resp.get("LastEvaluatedKey"),
    })

    return {"statusCode": 200, "body": "OK"}
