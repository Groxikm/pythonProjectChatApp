from abstractions.data_access import repository, data_entity
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo


class MongoRepository(repository.Repository):
    def __init__(self, mongo_connection_string: str, db_name: str, collection_name: str) -> None:
        # Create a new client and connect to the server, receive a collection
        self.collection = MongoClient(mongo_connection_string, server_api=ServerApi('1')).get_database(
            db_name).get_collection(collection_name)

    def create(self, entity: data_entity.AbstractEntity) -> dict:
        new_inserted_result = self.collection.insert_one(entity.to_db_dto())
        return self.collection.find_one({"_id": str(new_inserted_result.inserted_id)})

    def update(self, entity: data_entity.AbstractEntity) -> dict:
        db_dto = entity.to_db_dto().copy()
        db_dto.pop("_id")
        return self.collection.update_one({"_id": entity.get_id_str()}, {"$set": db_dto}, upsert=False)

    def delete(self, entity: data_entity.AbstractEntity):
        return self.collection.delete_one({"_id": entity.get_id_str()})

    def delete_by_id(self, id: str):
        return self.collection.delete_one({"_id": str(id)})

    def find_all_by_ids(self, ids: list[str]) -> list:
        cursor = self.collection.find({"_id": {"$in": ids}})
        result_list = []

        try:
            while (True):
                result_list.append(cursor.next())
        except StopIteration:
            print("stop iteration exception")
        except Exception:
            print("unwanted repository cursor exception")

        return result_list

    def find_by_id(self, id: str) -> list:
        return self.collection.find_one({"_id": id})

    # def find_all_by_page(self, start_from, page_size: int) -> dict:
    #     """will work well only with the entities with the 'date' field, with '%y/%m/%d %H:%M:%S' date format"""
    #     page_collection = []
    #     if start_from == "":
    #         cursor = self.collection.find().sort(key_or_list=[("date", pymongo.DESCENDING)]).limit(page_size)
    #     else:
    #         cursor = self.collection.find({"_id": {"$lt": str(start_from)}}).sort(
    #             key_or_list=[("date", pymongo.DESCENDING)]).limit(page_size)
    #
    #     i = 0
    #     try:
    #         while (i < page_size):
    #             page_collection.append(cursor.next())
    #             i += 1
    #     except StopIteration:
    #         print("stop iteration exception")
    #     except Exception:
    #         print("unwanted repository cursor exception")
    #
    #     return page_collection

    # def find_all_by_page(self, start_from, page_size: int) -> dict:
    #     """will be work well only with the entities with the 'date' field, with '%y/%m/%d %H:%M:%S' date format"""
    #     page_collection = []
    #     if start_from == "":
    #         cursor = self.collection.find().sort(key_or_list=[("date", pymongo.DESCENDING)]).limit(page_size)
    #     else:
    #         cursor = self.collection.find({"$lt": str(start_from)}).sort(
    #             key_or_list=[("date", pymongo.DESCENDING)]).limit(page_size)
    #
    #     i = 0
    #     try:
    #         while (i < page_size):
    #             page_collection.append(cursor.next())
    #             i += 1
    #     except StopIteration:
    #         print("stop iteration exception")
    #     except Exception:
    #         print("unwanted repository cursor exception")
    #
    #     return page_collection

    def find_all_by_page(self, start_from, page_size: int) -> list:
        """Fetches a paginated collection sorted first by 'date' and then by 'user_id' in descending order."""
        page_collection = []

        query = {}
        if start_from:
            query = {"date": {"$lt": start_from}}  # Filter by date, assuming start_from is a valid timestamp

        try:
            # Sort first by date DESC, then by user_id DESC
            cursor = self.collection.find(query).sort([("date", pymongo.DESCENDING),
                                                       ("_id", pymongo.DESCENDING)]).limit(page_size)

            for doc in cursor:
                page_collection.append(doc)

        except Exception as e:
            print(f"Error while fetching data: {e}")

        return page_collection
