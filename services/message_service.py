from typing import List, Dict, Any, Optional
from services.base_repository import BaseRepository
import datetime

class MessageService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_message(self, sender_id: str, group_id: str, content: str, message_type: str = "text") -> Dict[str, Any]:
        """Create a new message"""
        message_data = {
            "sender_id": sender_id,
            "group_id": group_id,
            "content": content,
            "type": message_type,
            "read_by": [sender_id],  # Sender has read the message
            "edited": False,
            "reply_to": None  # For replying to other messages
        }
        
        message_id = self.repository.create(message_data)
        return self.get_message(message_id)

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a single message by ID"""
        message = self.repository.find_by_id(message_id)
        return self._to_dto(message) if message else None

    def get_group_messages(self, group_id: str, limit: int = 50, before: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """Get messages for a specific group with pagination"""
        query = {"group_id": group_id}
        
        if before:
            query["created_at"] = {"$lt": before}
        
        messages = self.repository.find_many(
            query,
            sort_by=[("created_at", -1)],
            limit=limit
        )
        
        # Return in chronological order (oldest first)
        messages.reverse()
        return [self._to_dto(msg) for msg in messages]

    def edit_message(self, message_id: str, new_content: str, user_id: str) -> bool:
        """Edit a message (only sender can edit)"""
        message = self.repository.find_by_id(message_id)
        if not message or message.get("sender_id") != user_id:
            return False
        
        return self.repository.update_by_id(message_id, {
            "content": new_content,
            "edited": True
        })

    def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (only sender can delete)"""
        message = self.repository.find_by_id(message_id)
        if not message or message.get("sender_id") != user_id:
            return False
        
        return self.repository.delete_by_id(message_id)

    def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """Mark message as read by a user"""
        return self.repository.add_to_array(message_id, "read_by", user_id)

    def mark_group_messages_as_read(self, group_id: str, user_id: str, up_to_timestamp: Optional[datetime.datetime] = None) -> int:
        """Mark all messages in a group as read by a user up to a certain timestamp"""
        query = {
            "group_id": group_id,
            "read_by": {"$ne": user_id}
        }
        
        if up_to_timestamp:
            query["created_at"] = {"$lte": up_to_timestamp}
        
        result = self.repository.collection.update_many(
            query,
            {"$addToSet": {"read_by": user_id}}
        )
        
        return result.modified_count

    def get_unread_count(self, group_id: str, user_id: str) -> int:
        """Get count of unread messages for a user in a group"""
        return self.repository.count({
            "group_id": group_id,
            "read_by": {"$ne": user_id}
        })

    def get_unread_messages(self, user_id: str) -> Dict[str, int]:
        """Get unread message counts for all groups for a user"""
        pipeline = [
            {"$match": {"read_by": {"$ne": user_id}}},
            {"$group": {"_id": "$group_id", "count": {"$sum": 1}}}
        ]
        
        result = self.repository.collection.aggregate(pipeline)
        return {item["_id"]: item["count"] for item in result}

    def search_messages(self, group_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search messages in a group by content"""
        messages = self.repository.find_many(
            {
                "group_id": group_id,
                "content": {"$regex": query, "$options": "i"}
            },
            sort_by=[("created_at", -1)],
            limit=limit
        )
        
        return [self._to_dto(msg) for msg in messages]

    def create_reply(self, sender_id: str, group_id: str, content: str, reply_to_message_id: str, message_type: str = "text") -> Dict[str, Any]:
        """Create a reply to another message"""
        # Verify the original message exists and is in the same group
        original_message = self.repository.find_by_id(reply_to_message_id)
        if not original_message or original_message.get("group_id") != group_id:
            raise ValueError("Invalid message to reply to")
        
        message_data = {
            "sender_id": sender_id,
            "group_id": group_id,
            "content": content,
            "type": message_type,
            "read_by": [sender_id],
            "edited": False,
            "reply_to": reply_to_message_id
        }
        
        message_id = self.repository.create(message_data)
        return self.get_message(message_id)

    def get_message_thread(self, message_id: str) -> List[Dict[str, Any]]:
        """Get all replies to a specific message"""
        messages = self.repository.find_many(
            {"reply_to": message_id},
            sort_by=[("created_at", 1)]
        )
        
        return [self._to_dto(msg) for msg in messages]

    def get_recent_activity(self, group_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get recent activity stats for a group"""
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        
        message_count = self.repository.count({
            "group_id": group_id,
            "created_at": {"$gte": since}
        })
        
        # Get unique senders
        pipeline = [
            {"$match": {"group_id": group_id, "created_at": {"$gte": since}}},
            {"$group": {"_id": "$sender_id"}},
            {"$count": "unique_senders"}
        ]
        
        result = list(self.repository.collection.aggregate(pipeline))
        unique_senders = result[0]["unique_senders"] if result else 0
        
        return {
            "message_count": message_count,
            "unique_senders": unique_senders,
            "hours": hours
        }

    def get_messages_since(self, group_id: str, hours: int = 24) -> List[dict]:
        """Get messages from the last N hours"""
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        messages = self.repository.find_many(
            {"group_id": group_id, "created_at": {"$gte": since}},
            sort_by=[("created_at", 1)]
        )
        return [self._format_message(msg) for msg in messages]

    def _format_message(self, message: dict) -> dict:
        """Format message data for API response"""
        return {
            "id": str(message.get("_id", message.get("id", ""))),
            "sender_id": message.get("sender_id", ""),
            "group_id": message.get("group_id", ""),
            "content": message.get("content", ""),
            "type": message.get("type", "text"),
            "reply_to": message.get("reply_to"),
            "read_by": message.get("read_by", []),
            "edit_history": message.get("edit_history", []),
            "created_at": message.get("created_at", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "updated_at": message.get("updated_at", datetime.datetime.now(datetime.timezone.utc)).isoformat()
        }

    def _to_dto(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database message to DTO"""
        if not message:
            return None
        
        return {
            "id": str(message["_id"]),
            "sender_id": message["sender_id"],
            "group_id": message["group_id"],
            "content": message["content"],
            "type": message.get("type", "text"),
            "read_by": message.get("read_by", []),
            "edited": message.get("edited", False),
            "reply_to": message.get("reply_to"),
            "created_at": message.get("created_at", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "updated_at": message.get("updated_at", datetime.datetime.now(datetime.timezone.utc)).isoformat()
        } 