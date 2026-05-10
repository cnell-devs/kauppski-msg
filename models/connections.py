from dataclasses import dataclass
import time


@dataclass
class Connection:
    connection_id: str
    user_id: str
    ttl: int = 0

    def __post_init__(self):
        if not self.ttl:
            self.ttl = int(time.time()) + 86400

    def to_item(self) -> dict:
        return {
            "connectionId": self.connection_id,
            "userId": self.user_id,
            "ttl": self.ttl,
        }

    @classmethod
    def from_item(cls, item: dict) -> "Connection":
        return cls(
            connection_id=item["connectionId"],
            user_id=item["userId"],
            ttl=int(item.get("ttl", 0)),
        )
