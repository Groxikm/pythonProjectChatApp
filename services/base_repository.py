from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
import datetime
import certifi

class BaseRepository:
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        try:
            # Use certifi to provide up-to-date SSL certificates
            ca = certifi.where()
            
            # Initialize MongoDB client with proper configuration for PyMongo 4.6.1
            self.client = MongoClient(
                connection_string, 
                tlsCAFile=ca,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000,
                maxPoolSize=50,
                minPoolSize=5,
                retryWrites=True,
                w="majority"
            )
            
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            
            # Test the connection
            self.client.admin.command('ping')
            print(f"✓ Successfully connected to {collection_name} collection")
            
        except Exception as e:
            print(f"✗ Failed to connect to {collection_name} collection: {e}")
            raise e

    def create(self, data: Dict[str, Any]) -> str:
        """Create a new document and return its ID"""
        if "_id" not in data:
            data["created_at"] = datetime.datetime.now(datetime.timezone.utc)
        data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a document by its ID"""
        try:
            return self.collection.find_one({"_id": ObjectId(id)})
        except:
            return None

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching the query"""
        return self.collection.find_one(query)

    def find_many(self, query: Dict[str, Any], sort_by: Optional[List] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query"""
        cursor = self.collection.find(query)
        if sort_by:
            cursor = cursor.sort(sort_by)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_many_with_skip(self, query: Dict[str, Any], sort_by: Optional[List] = None, 
                           limit: Optional[int] = None, skip: int = 0) -> List[Dict[str, Any]]:
        """Find multiple documents matching the query with skip for pagination"""
        cursor = self.collection.find(query)
        if sort_by:
            cursor = cursor.sort(sort_by)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_by_id(self, id: str, data: Dict[str, Any]) -> bool:
        """Update a document by its ID"""
        data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update one document matching the query"""
        update.setdefault("$set", {})["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        result = self.collection.update_one(query, update)
        return result.modified_count > 0

    def delete_by_id(self, id: str) -> bool:
        """Delete a document by its ID"""
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    def add_to_array(self, id: str, field: str, value: Any) -> bool:
        """Add a value to an array field (using $addToSet to avoid duplicates)"""
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$addToSet": {field: value}, "$set": {"updated_at": datetime.datetime.now(datetime.timezone.utc)}}
        )
        return result.modified_count > 0

    def remove_from_array(self, id: str, field: str, value: Any) -> bool:
        """Remove a value from an array field"""
        result = self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$pull": {field: value}, "$set": {"updated_at": datetime.datetime.now(datetime.timezone.utc)}}
        )
        return result.modified_count > 0

    def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching the query"""
        if query is None:
            query = {}
        return self.collection.count_documents(query) 