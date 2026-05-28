import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from shared.auth import validate_token
from shared.dynamo import conversations_table


def _json_default(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_json_default),
    }


def handler(event, context):
    auth = (event.get("headers") or {}).get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return _resp(401, {"error": "Missing Bearer token"})

    try:
        user_id = validate_token(auth[7:])
    except ValueError as e:
        return _resp(403, {"error": str(e)})

    resp = conversations_table().query(
        IndexName="UserConversationsIndex",
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,  # newest first
    )

    return _resp(200, {"items": resp.get("Items", [])})
