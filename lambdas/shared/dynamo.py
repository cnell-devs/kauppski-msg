import os
import boto3

_resource = None


def get_resource():
    global _resource
    if _resource is None:
        _resource = boto3.resource("dynamodb")
    return _resource


def connections_table():
    return get_resource().Table(os.environ["CONNECTIONS_TABLE"])


def messages_table():
    return get_resource().Table(os.environ["MESSAGES_TABLE"])


def conversations_table():
    return get_resource().Table(os.environ["CONVERSATIONS_TABLE"])


def get_user_id_by_connection(connection_id: str) -> str | None:
    """Look up userId for an active connectionId."""
    resp = connections_table().get_item(Key={"connectionId": connection_id})
    item = resp.get("Item")
    return item["userId"] if item else None


def get_connection_id_by_user(user_id: str) -> str | None:
    """Look up active connectionId for a userId via GSI."""
    resp = connections_table().query(
        IndexName="UserIdIndex",
        KeyConditionExpression="userId = :uid",
        ExpressionAttributeValues={":uid": user_id},
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0]["connectionId"] if items else None
