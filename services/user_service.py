from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from services.base_repository import BaseRepository
import datetime

DEFAULT_PROFILE_PIC = "https://i.imgur.com/V4RclNb.png" # A generic user icon

class UserService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_user(self, username: str, password: str, profile_pic: str = "") -> Dict[str, Any]:
        """Create a new user with hashed password"""
        # Check if username already exists
        existing_user = self.repository.find_one({"username": username})
        if existing_user:
            raise ValueError("Username already exists")

        user_data = {
            "username": username,
            "password": generate_password_hash(password),
            "profile_pic": profile_pic or DEFAULT_PROFILE_PIC,
            "status": "offline",
            "friends": [],
            "last_active": datetime.datetime.now(datetime.timezone.utc),
            "is_typing_in": None  # group_id where user is currently typing, None if not typing
        }
        
        user_id = self.repository.create(user_data)
        return self.find_by_id(user_id)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        user = self.repository.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            # Update last active time and set status to online
            self.update_status(str(user["_id"]), "online")
            return self._to_dto(user)
        return None

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        user = self.repository.find_by_id(user_id)
        return self._to_dto(user) if user else None

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        user = self.repository.find_one({"username": username})
        return self._to_dto(user) if user else None

    def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Update user data (excluding password and sensitive fields)"""
        allowed_fields = ["username", "profile_pic"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return False
            
        return self.repository.update_by_id(user_id, update_data)

    def update_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Update user password with verification"""
        user = self.repository.find_by_id(user_id)
        if not user or not check_password_hash(user["password"], old_password):
            return False
        
        hashed_password = generate_password_hash(new_password)
        return self.repository.update_by_id(user_id, {"password": hashed_password})

    def update_status(self, user_id: str, status: str) -> bool:
        """Update user status and last active time"""
        return self.repository.update_by_id(user_id, {
            "status": status,
            "last_active": datetime.datetime.now(datetime.timezone.utc)
        })

    def add_friend(self, user_id: str, friend_id: str) -> bool:
        """Add a friend to user's friend list"""
        # Add friend to both users
        success1 = self.repository.add_to_array(user_id, "friends", friend_id)
        success2 = self.repository.add_to_array(friend_id, "friends", user_id)
        return success1 and success2

    def remove_friend(self, user_id: str, friend_id: str) -> bool:
        """Remove a friend from user's friend list"""
        # Remove friend from both users
        success1 = self.repository.remove_from_array(user_id, "friends", friend_id)
        success2 = self.repository.remove_from_array(friend_id, "friends", user_id)
        return success1 and success2

    def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's friends list with their details"""
        user = self.repository.find_by_id(user_id)
        if not user or "friends" not in user:
            return []
        
        friends = []
        for friend_id in user["friends"]:
            friend = self.find_by_id(friend_id)
            if friend:
                friends.append(friend)
        return friends

    def set_typing_status(self, user_id: str, group_id: str, is_typing: bool) -> bool:
        """Set user's typing status in a specific group"""
        if is_typing:
            return self.repository.add_to_array(user_id, "is_typing_in", group_id)
        else:
            return self.repository.remove_from_array(user_id, "is_typing_in", group_id)

    def get_online_users(self) -> List[Dict[str, Any]]:
        """Get all currently online users"""
        users = self.repository.find_many({"status": "online"})
        return [self._to_dto(user) for user in users]

    def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users by username"""
        users = self.repository.find_many(
            {"username": {"$regex": query, "$options": "i"}},
            limit=limit
        )
        return [self._to_dto(user) for user in users]

    def _to_dto(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database user to DTO (without password)"""
        if not user:
            return None
        
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "profile_pic": user.get("profile_pic", ""),
            "status": user.get("status", "offline"),
            "friends": user.get("friends", []),
            "last_active": user.get("last_active", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "is_typing_in": user.get("is_typing_in", None),
            "created_at": user.get("created_at", datetime.datetime.now(datetime.timezone.utc)).isoformat(),
            "updated_at": user.get("updated_at", datetime.datetime.now(datetime.timezone.utc)).isoformat()
        } 