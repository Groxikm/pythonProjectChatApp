from typing import List, Dict, Any, Optional
from mongo_orm.base_repository import BaseRepository
import datetime

class MessageService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_message(self, sender_id: str, group_id: str, content: str, message_type: str = "text") -> Dict[str, Any]:
        message_data = {
            "sender_id": sender_id,
            "group_id": group_id,
            "content": content,
            "type": message_type,
            "created_at": datetime.datetime.utcnow(),
            "read_by": [sender_id]
        }
        message_id = self.repository.create(message_data)
        message_data["_id"] = message_id
        return self._to_web_dto(message_data)

    def get_group_messages(self, group_id: str, limit: int = 50, before: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        query = {"group_id": group_id}
        if before:
            query["created_at"] = {"$lt": before}
        
        messages = self.repository.find_many(
            query,
            sort_by={"created_at": -1}
        )
        return [self._to_web_dto(msg) for msg in messages[:limit]]

    def mark_as_read(self, message_id: str, user_id: str) -> bool:
        return self.repository.add_to_array(message_id, "read_by", user_id)

    def get_unread_count(self, group_id: str, user_id: str) -> int:
        messages = self.repository.find_many({
            "group_id": group_id,
            "read_by": {"$ne": user_id}
        })
        return len(messages)

    def delete_message(self, message_id: str) -> bool:
        return self.repository.delete(message_id)

    def _to_web_dto(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not message:
            return None
        return {
            "id": str(message["_id"]),
            "sender_id": message["sender_id"],
            "group_id": message["group_id"],
            "content": message["content"],
            "type": message.get("type", "text"),
            "created_at": message["created_at"].isoformat(),
            "read_by": message.get("read_by", [])
        } 