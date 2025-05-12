from typing import List, Dict, Any, Optional
from mongo_orm.base_repository import BaseRepository
import datetime

class GroupService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_group(self, name: str, creator_id: str, is_private: bool = False, password: str = "") -> Dict[str, Any]:
        group_data = {
            "name": name,
            "creator_id": creator_id,
            "is_private": is_private,
            "password": password,
            "members": [creator_id],
            "admins": [creator_id],
            "created_at": datetime.datetime.utcnow()
        }
        group_id = self.repository.create(group_data)
        group_data["_id"] = group_id
        return self._to_web_dto(group_data)

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        group = self.repository.find_by_id(group_id)
        return self._to_web_dto(group) if group else None

    def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        groups = self.repository.find_many({"members": user_id})
        return [self._to_web_dto(group) for group in groups]

    def add_member(self, group_id: str, user_id: str) -> bool:
        return self.repository.add_to_array(group_id, "members", user_id)

    def remove_member(self, group_id: str, user_id: str) -> bool:
        success = self.repository.remove_from_array(group_id, "members", user_id)
        if success:
            self.repository.remove_from_array(group_id, "admins", user_id)
        return success

    def add_admin(self, group_id: str, user_id: str) -> bool:
        # First ensure user is a member
        if not self.repository.find_one({"_id": group_id, "members": user_id}):
            return False
        return self.repository.add_to_array(group_id, "admins", user_id)

    def remove_admin(self, group_id: str, user_id: str) -> bool:
        return self.repository.remove_from_array(group_id, "admins", user_id)

    def update_group(self, group_id: str, data: Dict[str, Any]) -> bool:
        return self.repository.update(group_id, data)

    def delete_group(self, group_id: str) -> bool:
        return self.repository.delete(group_id)

    def is_member(self, group_id: str, user_id: str) -> bool:
        group = self.repository.find_one({"_id": group_id, "members": user_id})
        return bool(group)

    def is_admin(self, group_id: str, user_id: str) -> bool:
        group = self.repository.find_one({"_id": group_id, "admins": user_id})
        return bool(group)

    def _to_web_dto(self, group: Dict[str, Any]) -> Dict[str, Any]:
        if not group:
            return None
        return {
            "id": str(group["_id"]),
            "name": group["name"],
            "creator_id": group["creator_id"],
            "is_private": group.get("is_private", False),
            "members": group.get("members", []),
            "admins": group.get("admins", []),
            "created_at": group["created_at"].isoformat()
        } 