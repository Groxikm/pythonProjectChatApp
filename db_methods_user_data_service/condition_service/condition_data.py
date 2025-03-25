import abstractions.data_access.data_entity
import abstractions.data_transfer
import uuid
import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class ConditionData(abstractions.data_access.data_entity.AbstractEntity, abstractions.data_transfer.Exchangeable):

    def __init__(self, id: str, days_scope: int, days_limit: int, attendance: int, backlog_limit: str) -> None:
        self.id = id
        self.days_scope = days_scope
        self.days_limit = days_limit
        self.attendance = attendance
        self.backlog_limit = backlog_limit

    def from_web_dto(dto: dict):
        if dto.keys().__contains__("id") == True:
            if (dto.get("id") != None) or (dto.get("id") != ""):
                return ConditionData(dto.get("id"), dto.get("days_scope"), dto.get("days_limit"), dto.get("attendance"), dto.get("backlog_limit"))

        return ConditionData(uuid.uuid1(), dto.get("days_scope"), dto.get("days_limit"), dto.get("attendance"), dto.get("backlog_limit"))

    def get_id_str(self) -> str:
        return str(self.id)

    def to_web_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "days_scope": self.days_scope,
            "days_limit": self.days_limit,
            "attendance": self.attendance,
            "backlog_limit": self.backlog_limit
        }

    def to_db_dto(self) -> dict:
        return {
            "_id": self.get_id_str(),
            "days_scope": self.days_scope,
            "days_limit": self.days_limit,
            "attendance": self.attendance,
            "backlog_limit": self.backlog_limit
        }


def from_db_dto(dto: dict) -> ConditionData:
    return ConditionData(dto.get("_id"), dto.get("days_scope"), dto.get("days_limit"), dto.get("attendance"), dto.get("backlog_limit"))
