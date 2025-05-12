from abc import abstractmethod, ABC
import db_methods_user_data_service.messages_data_service.messages_data as messagesData
from abstractions.data_access import repository
import pymongo
from db_methods_user_data_service.messages_data_service.messages_data import from_db_dto

import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class MessagesDataService:
    def __init__(self, repo: repository.Repository) -> None:
        self._repo = repo
        self.collection = self._repo.collection

    def add_new(self, messagesData_dto: dict) -> messagesData.MessagesData:
        return messagesData.from_db_dto(self._repo.create(messagesData.MessagesData.from_web_dto(messagesData_dto)))

    def delete(self, id: str) -> None:
        self._repo.delete_by_id(id)

    def find_by_id(self, id: str) -> messagesData.MessagesData:
        return messagesData.from_db_dto(self._repo.find_by_id(id))

    def find_all_by_id(self, start_from, page_size: int, user_id: str) -> list:
        page_collection = list()
        # print(type(start_from), page_size)
        query = {"user_id": user_id}
        if start_from:
            query["date"] = {"$lt": start_from}

        try:
            cursor = self.collection.find(query).sort([("date", pymongo.DESCENDING)]).limit(page_size)

            for doc in cursor:
                page_collection.append(from_db_dto(doc))
                if len(page_collection) >= page_size:
                    break  # Stop when enough elements are collected

        except Exception as e:
            print(f"Error while fetching data: {e}")

        return page_collection

    # this is a pagination method which uses start_from as a value for filtering
    def find_all_by_page(self, start_from, page_size: int = 10) -> list:
        page_collection = list()
        query = {}
        if start_from:
            query["date"] = {"$lt": start_from}

        try:
            cursor = self.collection.find(query).sort([("date", pymongo.DESCENDING)]).limit(page_size)

            for doc in cursor:
                page_collection.append(from_db_dto(doc))
                if len(page_collection) >= page_size:
                    break  # Stop when enough elements are collected

        except Exception as e:
            print(f"Error while fetching data: {e}")

        return page_collection


    def find_by_room_id(self, start_from, page_size: int, room_id: str) -> list:
        """Find messages by room ID with pagination support"""
        page_collection = list()
        query = {"room_id": room_id}
        if start_from:
            query["date"] = {"$lt": start_from}

        try:
            cursor = self.collection.find(query).sort([("date", pymongo.DESCENDING)]).limit(page_size)

            for doc in cursor:
                page_collection.append(from_db_dto(doc))
                if len(page_collection) >= page_size:
                    break  # Stop when enough elements are collected
        except Exception as e:
            print(f"Error while fetching messages by room_id: {e}")

        return page_collection








