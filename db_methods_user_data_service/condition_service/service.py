from abc import abstractmethod, ABC
import db_methods_user_data_service.condition_service.condition_data as conditionData
from abstractions.data_access import repository
import pymongo
from db_methods_user_data_service.condition_service.condition_data import from_db_dto


class ConditionDataService:
    def __init__(self, repo: repository.Repository) -> None:
        self._repo = repo
        self.collection = self._repo.collection

    def add_new(self, conditionData_dto: dict) -> conditionData.ConditionData:
        return conditionData.from_db_dto(self._repo.create(conditionData.ConditionData.from_web_dto(conditionData_dto)))

    def update(self, conditionData_dto: dict) -> conditionData.ConditionData:
        self._repo.update(conditionData.ConditionData.from_web_dto(conditionData_dto))
        conditionData_obj = conditionData.from_db_dto(self._repo.find_by_id(conditionData_dto.get("id")))
        print("Status rules changed")
        return conditionData_obj

    def delete(self, id: str) -> None:
        self._repo.delete_by_id(id)

    def find_by_id(self, id: str) -> conditionData.ConditionData:
        return conditionData.from_db_dto(self._repo.find_by_id(id))
