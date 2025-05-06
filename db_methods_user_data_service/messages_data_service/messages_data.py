import abstractions.data_access.data_entity
import abstractions.data_transfer
import uuid
import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class MessagesData(abstractions.data_access.data_entity.AbstractEntity, abstractions.data_transfer.Exchangeable):

    def __init__(self, id: str, user_id: str, room_id: str, location: str, status: str, role: str, date: datetime.datetime) -> None:
        self.id = id
        self.user_id = user_id
        self.room_id = room_id
        self.location = location
        self.status = status
        self.role = role
        self.date = date

    def from_web_dto(dto: dict):
        if dto.keys().__contains__("id") == True:
            if (dto.get("id") != None) or (dto.get("id") != ""):
                return MessagesData(dto.get("id"), dto.get("user_id"), dto.get("room_id"), dto.get("location"), dto.get("status"), dto.get("role"),
                                 datetime.datetime.strptime(dto.get("date"), DATE_FORMAT))

        return MessagesData(uuid.uuid1(), dto.get("user_id"), dto.get("location"), dto.get("status"), dto.get("role"), datetime.datetime.now())

    def get_id_str(self) -> str:
        return str(self.id)

    def to_web_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "user_id": self.user_id,
            "room_id": self.room_id,
            "location": self.location,
            "status": self.status,
            "role": self.role,
            "date": self.date.strftime(DATE_FORMAT)
        }

    def to_db_dto(self) -> dict:
        return {
            "_id": self.get_id_str(),
            "user_id": self.user_id,
            "room_id": self.room_id,
            "location": self.location,
            "status": self.status,
            "role": self.role,
            "date": self.date.strftime(DATE_FORMAT)
        }


def from_db_dto(dto: dict) -> MessagesData:
    return MessagesData(dto.get("_id"), dto.get("user_id"), dto.get("room_id"), dto.get("location"),  dto.get("status"), dto.get("role"),
                            datetime.datetime.strptime(dto.get("date"), DATE_FORMAT))
