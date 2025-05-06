import abstractions.data_access.data_entity
import abstractions.data_transfer
import uuid
import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class UserData(abstractions.data_access.data_entity.AbstractEntity, abstractions.data_transfer.Exchangeable):

    def __init__(self, id: str, global_role: str, username: str, password: str,
                 profile_pic: str, status: str, friends: list, last_active_date: datetime.datetime, date: datetime.datetime) -> None:
        self.id = id
        self.global_role = global_role
        self.username = username
        self.password = password
        self.profile_pic = profile_pic
        self.status = status
        self.friends = friends
        self.last_active_date = last_active_date
        self.date = date

    def from_web_dto(dto: dict):
        if dto.keys().__contains__("id") == True:
            if (dto.get("id") != None) or (dto.get("id") != ""):
                return UserData(dto.get("id"),

                                dto.get("global_role"), dto.get("username"), dto.get("password"), dto.get("profile_pic"), dto.get("status"),

                                datetime.datetime.strptime(dto.get("last_active_date"), DATE_FORMAT), datetime.datetime.strptime(dto.get("date"), DATE_FORMAT))

        return UserData(uuid.uuid1(),

                                dto.get("global_role"), dto.get("username"), dto.get("password"), dto.get("profile_pic"),
                                dto.get("status"),

                                datetime.datetime.now(), datetime.datetime.now() )

    def get_id_str(self) -> str:
        return str(self.id)

    def to_web_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "global_role": self.global_role,
            "username": self.username,
            "profile_pic": self.profile_pic,

            "status": self.status,
            "friends": self.friends, # list []
            "last_active_date": self.last_active_date.strftime(DATE_FORMAT), # date format YYYY-MM-DD
            "date": self.date.strftime(DATE_FORMAT) # date format YYYY-MM-DD

        }

    def to_db_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "global_role": self.global_role,
            "username": self.username,
            "profile_pic": self.profile_pic,
            "password": self.password,
            "status": self.status,
            "friends": self.friends, # list []
            "last_active_date": self.last_active_date.strftime(DATE_FORMAT), # date format YYYY-MM-DD
            "date": self.date.strftime(DATE_FORMAT) # date format YYYY-MM-DD
        }


def from_db_dto(dto: dict) -> UserData:
    return UserData(dto.get("_id"),

                    dto.get("global_role"), dto.get("username"), dto.get("password"), dto.get("profile_pic"),
                    dto.get("status"),

                    datetime.datetime.strptime(dto.get("last_active_date"), DATE_FORMAT),
                    datetime.datetime.strptime(dto.get("date"), DATE_FORMAT)
                    )