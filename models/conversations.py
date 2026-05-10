from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Conversation:
    user_id: str
    conversation_id: str
    other_user_id: str
    updated_at: str = ""
    last_message: str = ""
    unread_count: int = 0

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_item(self) -> dict:
        return {
            "userId": self.user_id,
            "conversationId": self.conversation_id,
            "otherUserId": self.other_user_id,
            "updatedAt": self.updated_at,
            "lastMessage": self.last_message,
            "unreadCount": self.unread_count,
        }

    @classmethod
    def from_item(cls, item: dict) -> "Conversation":
        return cls(
            user_id=item["userId"],
            conversation_id=item["conversationId"],
            other_user_id=item["otherUserId"],
            updated_at=item.get("updatedAt", ""),
            last_message=item.get("lastMessage", ""),
            unread_count=int(item.get("unreadCount", 0)),
        )


def build_conversation_id(user_a: str, user_b: str) -> str:
    return "#".join(sorted([user_a, user_b]))
