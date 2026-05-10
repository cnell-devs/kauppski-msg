import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.dynamo import connections_table


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    connections_table().delete_item(Key={"connectionId": connection_id})
    return {"statusCode": 200, "body": "Disconnected"}
