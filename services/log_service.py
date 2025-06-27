from typing import List, Dict, Any, Optional
from services.base_repository import BaseRepository
import datetime

class LogService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def create_log(self, message: str, url: str, level: str = "INFO", extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new log entry"""
        log_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "level": level,
            "message": message,
            "url": url,
            "extra_data": extra_data or {}
        }
        return self.repository.create(log_data)

    def get_logs(self, limit: int = 100, level: Optional[str] = None, before: Optional[datetime.datetime] = None, 
                 skip: int = 0) -> Dict[str, Any]:
        """Get logs with pagination and filtering"""
        query = {}
        if level:
            query["level"] = level.upper()
        
        if before:
            query["timestamp"] = {"$lt": before}
        
        # Get total count for pagination info
        total_count = self.repository.count(query)
        
        # Get the logs with pagination
        logs = self.repository.find_many_with_skip(
            query,
            sort_by=[("timestamp", -1)],
            limit=limit,
            skip=skip
        )
        
        return {
            "logs": [self._to_dto(log) for log in logs],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "skip": skip,
                "has_more": skip + limit < total_count
            }
        }

    def get_logs_simple(self, limit: int = 100, level: Optional[str] = None, before: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """Get logs with simple pagination (backward compatibility)"""
        query = {}
        if level:
            query["level"] = level.upper()
        
        if before:
            query["timestamp"] = {"$lt": before}
            
        logs = self.repository.find_many(
            query,
            sort_by=[("timestamp", -1)],
            limit=limit
        )
        return [self._to_dto(log) for log in logs]

    def _to_dto(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database log to DTO"""
        if not log:
            return None
        
        return {
            "id": str(log["_id"]),
            "timestamp": log["timestamp"].isoformat(),
            "level": log["level"],
            "message": log["message"],
            "url": log["url"],
            "extra_data": log.get("extra_data", {})
        } 