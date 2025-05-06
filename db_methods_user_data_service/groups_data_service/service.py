from abc import abstractmethod, ABC
import db_methods_user_data_service.groups_data_service.groups_data as groupsData
from abstractions.data_access import repository
import pymongo
from db_methods_user_data_service.groups_data_service.groups_data import from_db_dto


class GroupsDataService:
    def __init__(self, repo: repository.Repository) -> None:
        self._repo = repo
        self.collection = self._repo.collection

    def add_new(self, groupsData_dto: dict) -> groupsData.GroupsData:
        return groupsData.from_db_dto(self._repo.create(groupsData.GroupsData.from_web_dto(groupsData_dto)))

    def update(self, groupsData_dto: dict) -> groupsData.GroupsData:
        self._repo.update(groupsData.GroupsData.from_web_dto(groupsData_dto))
        groupsData_obj = groupsData.from_db_dto(self._repo.find_by_id(groupsData_dto.get("id")))
        return groupsData_obj

    def delete(self, id: str) -> None:
        self._repo.delete_by_id(id)

    def find_by_id(self, id: str) -> groupsData.GroupsData:
        return groupsData.from_db_dto(self._repo.find_by_id(id))
