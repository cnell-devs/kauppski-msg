import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from boto3.dynamodb.conditions import Key
from shared.dynamo import conversations_table, get_user_id_by_connection
from shared.ws import reply


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]

    user_id = get_user_id_by_connection(connection_id)
    if not user_id:
        return {"statusCode": 403, "body": "Unknown connection"}

    resp = conversations_table().query(
        IndexName="UserConversationsIndex",
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,  # newest first
    )

    reply(connection_id, "conversations", {
        "items": resp.get("Items", []),
    })

    return {"statusCode": 200, "body": "OK"}
