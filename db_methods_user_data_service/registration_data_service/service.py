from abc import abstractmethod, ABC
import db_methods_user_data_service.registration_data_service.registration_data as registrationData
from abstractions.data_access import repository
import pymongo
from db_methods_user_data_service.registration_data_service.registration_data import from_db_dto

import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class RegistrationDataService:
    def __init__(self, repo: repository.Repository) -> None:
        self._repo = repo
        self.collection = self._repo.collection

    def add_new(self, registrationData_dto: dict) -> registrationData.RegistrationData:
        return registrationData.from_db_dto(self._repo.create(registrationData.RegistrationData.from_web_dto(registrationData_dto)))

    def delete(self, id: str) -> None:
        self._repo.delete_by_id(id)

    def find_by_id(self, id: str) -> registrationData.RegistrationData:
        return registrationData.from_db_dto(self._repo.find_by_id(id))

    def find_all_by_id(self, start_from, page_size: int, user_id: str) -> list:
        page_collection = list()
        print(type(start_from), page_size)
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

    def find_all_by_page(self, start_from, page_size: int) -> list:
        page_collection = list()
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