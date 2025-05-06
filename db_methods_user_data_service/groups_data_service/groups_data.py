import abstractions.data_access.data_entity
import abstractions.data_transfer
import uuid
import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class GroupsData(abstractions.data_access.data_entity.AbstractEntity, abstractions.data_transfer.Exchangeable):

    def __init__(self, id: str, name: str, creator_id: str, participants: list, password: str, admins: list) -> None:
        self.id = id
        self.name = name
        self.creator_id = creator_id
        self.participants = participants
        self.password = password
        self.admins = admins

    def from_web_dto(dto: dict):
        if dto.keys().__contains__("id") == True:
            if (dto.get("id") != None) or (dto.get("id") != ""):
                return GroupsData(dto.get("id"), dto.get("name"), dto.get("creator_id"), dto.get("participants"), dto.get("password"),
                                    dto.get("admins"),
                                    datetime.datetime.strptime(dto.get("date"), DATE_FORMAT))

        return GroupsData(uuid.uuid1(), dto.get("name"), dto.get("creator_id"), dto.get("participants"), dto.get("password"), dto.get("admins"),
                            datetime.datetime.now())

    def get_id_str(self) -> str:
        return str(self.id)

    def to_web_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "name": self.name,
            "creator_id": self.creator_id,
            "participants": self.participants,
            "password": self.password,
            "admins": self.admins
        }

    def to_db_dto(self) -> dict:
        return {
            "_id": self.get_id_str(),
            "name": self.name,
            "creator_id": self.creator_id,
            "participants": self.participants,
            "password": self.password,
            "admins": self.admins
        }


def from_db_dto(dto: dict) -> GroupsData:
    return GroupsData(dto.get("_id"), dto.get("name"), dto.get("creator_id"), dto.get("participants"), dto.get("password"),
                      dto.get("admins"))