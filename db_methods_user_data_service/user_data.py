import abstractions.data_access.data_entity
import abstractions.data_transfer
import uuid
import datetime

DATE_FORMAT = "%y/%m/%d %H:%M:%S"


class UserData(abstractions.data_access.data_entity.AbstractEntity, abstractions.data_transfer.Exchangeable):

    def __init__(self, id: str, club: str, team: str, role: str, name: str, surname: str, login: str, password: str,
                 visit_frequency: int, backlog: int,  avatar_link: str, club_link: str, date: datetime.datetime) -> None:
        self.id = id
        self.club = club
        self.team = team
        self.role = role
        self.name = name
        self.surname = surname
        self.login = login
        self.password = password
        self.visit_frequency = visit_frequency
        self.backlog = backlog
        self.avatar_link = avatar_link
        self.club_link = club_link

        self.date = date

    def from_web_dto(dto: dict):
        if dto.keys().__contains__("id") == True:
            if (dto.get("id") != None) or (dto.get("id") != ""):
                return UserData(dto.get("id"),

                                dto.get("club"), dto.get("team"), dto.get("role"), dto.get("name"), dto.get("surname"), dto.get("login"), dto.get("password"),
                                dto.get("visit_frequency"), dto.get("backlog"), dto.get("avatar_link"), dto.get("club_link"),

                                datetime.datetime.strptime(dto.get("date"), DATE_FORMAT))

        return UserData(uuid.uuid1(),

                                dto.get("club"), dto.get("team"), dto.get("role"),  dto.get("name"), dto.get("surname"), dto.get("login"), dto.get("password"),
                                dto.get("visit_frequency"), dto.get("backlog"), dto.get("avatar_link"), dto.get("club_link"),

                                datetime.datetime.now())

    def get_id_str(self) -> str:
        return str(self.id)

    def to_web_dto(self) -> dict:
        return {
            "id": self.get_id_str(),
            "club": self.club,
            "team": self.team,
            "role": self.role,
            "name": self.name,
            "surname": self.surname,
            "login": self.login,
            "visit_frequency": self.visit_frequency,
            "backlog": self.backlog,
            "avatar_link": self.avatar_link,
            "club_link": self.club_link,
            "date": self.date.strftime(DATE_FORMAT)

        }

    def to_db_dto(self) -> dict:
        return {
            "_id": self.get_id_str(),
            "club": self.club,
            "team": self.team,
            "role": self.role,
            "name": self.name,
            "surname": self.surname,
            "login": self.login,
            "password": self.password,
            "visit_frequency": self.visit_frequency,
            "backlog": self.backlog,
            "avatar_link": self.avatar_link,
            "club_link": self.club_link,
            "date": self.date.strftime(DATE_FORMAT)
        }


def from_db_dto(dto: dict) -> UserData:
    return UserData(dto.get("_id"),
                    dto.get("club"), dto.get("team"), dto.get("role"), dto.get("name"), dto.get("surname"), dto.get("login"), dto.get("password"),
                    dto.get("visit_frequency"), dto.get("backlog"), dto.get("avatar_link"), dto.get("club_link"),

                    datetime.datetime.strptime(dto.get("date"), DATE_FORMAT)
                    )