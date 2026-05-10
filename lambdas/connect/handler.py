import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from shared.auth import validate_token
from shared.dynamo import connections_table


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    params = event.get("queryStringParameters") or {}
    token = params.get("token")

    if not token:
        return {"statusCode": 401, "body": "Missing token"}

    try:
        user_id = validate_token(token)
    except ValueError:
        return {"statusCode": 403, "body": "Invalid token"}

    connections_table().put_item(
        Item={
            "connectionId": connection_id,
            "userId": user_id,
            "ttl": int(time.time()) + 86400,
        }
    )

    return {"statusCode": 200, "body": "Connected"}
