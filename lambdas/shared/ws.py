import os
import json
import boto3
from botocore.exceptions import ClientError

_client = None


def get_client():
    global _client
    if _client is None:
        endpoint = os.environ["APIGW_ENDPOINT"]
        _client = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint)
    return _client


def post_to_connection(connection_id: str, data: dict) -> bool:
    """Send JSON data to a WebSocket connection. Returns False if connection is gone."""
    try:
        get_client().post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode("utf-8"),
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("GoneException", "410"):
            return False
        raise


def reply(connection_id: str, action: str, payload: dict):
    """Send a typed response envelope back to the caller."""
    post_to_connection(connection_id, {"action": action, "data": payload})
