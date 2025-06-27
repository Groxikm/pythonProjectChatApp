from typing import List, Dict, Any, Optional
from services.base_repository import BaseRepository
import datetime
from bson import ObjectId

class GroupService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_group(self, name: str, creator_id: str, description: str = "", is_private: bool = False) -> Dict[str, Any]:
        """Create a new group/chat room"""
        group_data = {
            "name": name,
            "description": description,
            "creator_id": creator_id,
            "is_private": is_private,
            "members": [creator_id],
            "admins": [creator_id],
            "typing_users": [],  # Users currently typing in this group
            "last_activity": datetime.datetime.now(datetime.timezone.utc)
        }
        
        group_id = self.repository.create(group_data)
        return self.get_group(group_id)

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group details by ID"""
        group = self.repository.find_by_id(group_id)
        return self._to_dto(group) if group else None

    def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all groups where user is a member"""
        groups = self.repository.find_many(
            {"members": user_id},
            sort_by=[("last_activity", -1)]
        )
        return [self._to_dto(group) for group in groups]

    def get_public_groups(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get public groups that can be joined"""
        groups = self.repository.find_many(
            {"is_private": False},
            sort_by=[("last_activity", -1)],
            limit=limit
        )
        return [self._to_dto(group) for group in groups]

    def add_member(self, group_id: str, user_id: str) -> bool:
        """Add a member to the group"""
        return self.repository.add_to_array(group_id, "members", user_id)

    def remove_member(self, group_id: str, user_id: str) -> bool:
        """Remove a member from the group"""
        # Remove from members and admins
        success1 = self.repository.remove_from_array(group_id, "members", user_id)
        success2 = self.repository.remove_from_array(group_id, "admins", user_id)
        return success1

    def add_admin(self, group_id: str, user_id: str, requester_id: str) -> bool:
        """Add an admin to the group (only existing admins can do this)"""
        if not self.is_admin(group_id, requester_id):
            return False
        
        # User must be a member first
        if not self.is_member(group_id, user_id):
            return False
            
        return self.repository.add_to_array(group_id, "admins", user_id)

    def remove_admin(self, group_id: str, user_id: str, requester_id: str) -> bool:
        """Remove an admin from the group"""
        group = self.repository.find_by_id(group_id)
        if not group:
            return False
            
        # Can't remove the creator
        if group.get("creator_id") == user_id:
            return False
            
        # Only admins can remove other admins
        if not self.is_admin(group_id, requester_id):
            return False
            
        return self.repository.remove_from_array(group_id, "admins", user_id)

    def update_group(self, group_id: str, data: Dict[str, Any], requester_id: str) -> bool:
        """Update group details (only admins can do this)"""
        if not self.is_admin(group_id, requester_id):
            return False
            
        allowed_fields = ["name", "description", "is_private"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return False
            
        return self.repository.update_by_id(group_id, update_data)

    def delete_group(self, group_id: str, requester_id: str) -> bool:
        """Delete a group (only creator can do this)"""
        group = self.repository.find_by_id(group_id)
        if not group or group.get("creator_id") != requester_id:
            return False
            
        return self.repository.delete_by_id(group_id)

    def is_member(self, group_id: str, user_id: str) -> bool:
        """Check if user is a member of the group"""
        try:
            group = self.repository.find_one({"_id": ObjectId(group_id), "members": user_id})
            return bool(group)
        except Exception:
            return False

    def is_admin(self, group_id: str, user_id: str) -> bool:
        """Check if user is an admin of the group"""
        try:
            group = self.repository.find_one({"_id": ObjectId(group_id), "admins": user_id})
            return bool(group)
        except Exception:
            return False

    def update_last_activity(self, group_id: str) -> bool:
        """Update the last activity timestamp for the group"""
        return self.repository.update_by_id(group_id, {
            "last_activity": datetime.datetime.now(datetime.timezone.utc)
        })

    def set_user_typing(self, group_id: str, user_id: str, is_typing: bool) -> bool:
        """Set user typing status in the group"""
        if is_typing:
            return self.repository.add_to_array(group_id, "typing_users", user_id)
        else:
            return self.repository.remove_from_array(group_id, "typing_users", user_id)

    def get_typing_users(self, group_id: str) -> List[str]:
        """Get list of users currently typing in the group"""
        group = self.repository.find_by_id(group_id)
        return group.get("typing_users", []) if group else []

    def search_groups(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search public groups by name"""
        groups = self.repository.find_many(
            {
                "name": {"$regex": query, "$options": "i"},
                "is_private": False
            },
            sort_by=[("last_activity", -1)],
            limit=limit
        )
        return [self._to_dto(group) for group in groups]

    def get_group_members(self, group_id: str) -> List[str]:
        """Get list of group member IDs"""
        group = self.repository.find_by_id(group_id)
        return group.get("members", []) if group else []

    def _to_dto(self, group: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database group to DTO"""
        if not group:
            return None
            
        return {
            "id": str(group["_id"]),
            "name": group["name"],
            "description": group.get("description", ""),
            "creator_id": group["creator_id"],
            "is_private": group.get("is_private", False),
            "members": group.get("members", []),
            "admins": group.get("admins", []),
            "member_count": len(group.get("members", [])),
            "typing_users": group.get("typing_users", []),
            "last_activity": group.get("last_activity", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "created_at": group.get("created_at", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "updated_at": group.get("updated_at", datetime.datetime.now(datetime.timezone.utc)).isoformat()
        } 