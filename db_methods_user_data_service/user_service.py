from typing import Optional, Dict, Any, List
from mongo_orm.base_repository import BaseRepository
import datetime

class UserService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_user(self, username: str, password: str, profile_pic: str = "") -> Dict[str, Any]:
        user_data = {
            "username": username,
            "password": password,
            "profile_pic": profile_pic,
            "status": "offline",
            "friends": [],
            "last_active": datetime.datetime.utcnow()
        }
        user_id = self.repository.create(user_data)
        user_data["_id"] = user_id
        return self._to_web_dto(user_data)

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        user = self.repository.find_one({"username": username})
        return self._to_web_dto(user) if user else None

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = self.repository.find_by_id(user_id)
        return self._to_web_dto(user) if user else None

    def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        return self.repository.update(user_id, data)

    def update_status(self, user_id: str, status: str) -> bool:
        return self.repository.update(user_id, {
            "status": status,
            "last_active": datetime.datetime.utcnow()
        })

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        return self.repository.add_to_array(user_id, "friends", friend_id)

    def remove_friend(self, user_id: str, friend_id: str) -> bool:
        return self.repository.remove_from_array(user_id, "friends", friend_id)

    def get_friends(self, user_id: str) -> List[str]:
        user = self.repository.find_by_id(user_id)
        return user.get("friends", []) if user else []

    def _to_web_dto(self, user: Dict[str, Any]) -> Dict[str, Any]:
        if not user:
            return None
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "profile_pic": user.get("profile_pic", ""),
            "status": user.get("status", "offline"),
            "friends": user.get("friends", []),
            "last_active": user.get("last_active", datetime.datetime.utcnow()).isoformat()
        } 