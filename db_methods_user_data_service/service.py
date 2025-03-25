from abc import abstractmethod, ABC
import db_methods_user_data_service.user_data as userData
from abstractions.data_access import repository
import pymongo
from db_methods_user_data_service.user_data import from_db_dto

import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"

class UserDataService:
    def __init__(self, repo: repository.Repository) -> None:
        self._repo = repo
        self.collection = self._repo.collection

    def add_new(self, userData_dto: dict) -> userData.UserData:
        return userData.from_db_dto(self._repo.create(userData.UserData.from_web_dto(userData_dto)))

    def update(self, userData_dto: dict) -> userData.UserData:
        self._repo.update(userData.UserData.from_web_dto(userData_dto))
        userData_obj = userData.from_db_dto(self._repo.find_by_id(userData_dto.get("id")))
        return userData_obj

    def delete(self, id: str) -> None:
        self._repo.delete_by_id(id)

    def find_by_id(self, id: str) -> userData.UserData:
        return userData.from_db_dto(self._repo.find_by_id(id))

    def find_by_name_surname(self, name: str, surname: str) -> userData.UserData:
        user_data_db_dto = self.collection.find_one({"name": name, "surname": surname})
        # print("user_data_db_dto is equal:")
        # print(user_data_db_dto)
        return userData.from_db_dto(user_data_db_dto)

    def find_by_login(self, login: str) -> userData.UserData:
        user_data_db_dto = self.collection.find_one({"login": login})
        return userData.from_db_dto(user_data_db_dto)

    def find_all_by_page(self, start_from=None, page_size: int =10) -> list:
        page_collection = []

        query = {"role": "USER"}
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



