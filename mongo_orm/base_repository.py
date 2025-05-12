from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
import datetime

class BaseRepository:
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.collection.find_one({"_id": ObjectId(id)})
        except:
            return None

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.collection.find_one(query)

    def find_many(self, query: Dict[str, Any], sort_by: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(query)
        if sort_by:
            cursor = cursor.sort(sort_by)
        return list(cursor)

    def create(self, data: Dict[str, Any]) -> str:
        data["created_at"] = datetime.datetime.utcnow()
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def update(self, id: str, data: Dict[str, Any]) -> bool:
        data["updated_at"] = datetime.datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    def delete(self, id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    def add_to_array(self, id: str, field: str, value: Any) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$addToSet": {field: value}}
        )
        return result.modified_count > 0

    def remove_from_array(self, id: str, field: str, value: Any) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$pull": {field: value}}
        )
        return result.modified_count > 0 