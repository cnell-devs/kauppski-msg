from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Message:
    conversation_id: str
    sender_id: str
    content: str
    message_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def sort_key(self) -> str:
        return f"{self.created_at}#{self.message_id}"

    def to_item(self) -> dict:
        return {
            "conversationId": self.conversation_id,
            "sk": self.sort_key,
            "senderId": self.sender_id,
            "content": self.content,
            "createdAt": self.created_at,
            "messageId": self.message_id,
        }

    @classmethod
    def from_item(cls, item: dict) -> "Message":
        return cls(
            conversation_id=item["conversationId"],
            sender_id=item["senderId"],
            content=item["content"],
            message_id=item.get("messageId", ""),
            created_at=item.get("createdAt", ""),
        )
