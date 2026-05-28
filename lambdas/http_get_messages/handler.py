import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from shared.auth import validate_token
from shared.dynamo import messages_table


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

    conversation_id = (event.get("pathParameters") or {}).get("conversationId", "")
    if not conversation_id:
        return _resp(400, {"error": "conversationId path parameter required"})

    parts = conversation_id.split("#")
    if len(parts) != 3 or user_id not in parts[:2]:
        return _resp(403, {"error": "Not a participant"})

    qs = event.get("queryStringParameters") or {}
    last_key = qs.get("lastKey")

    query_kwargs = dict(
        KeyConditionExpression=Key("conversationId").eq(conversation_id),
        ScanIndexForward=True,
        Limit=50,
    )
    if last_key:
        query_kwargs["ExclusiveStartKey"] = json.loads(last_key)

    resp = messages_table().query(**query_kwargs)

    next_key = resp.get("LastEvaluatedKey")
    return _resp(200, {
        "conversationId": conversation_id,
        "items": resp.get("Items", []),
        "nextKey": json.dumps(next_key, default=_json_default) if next_key else None,
    })
