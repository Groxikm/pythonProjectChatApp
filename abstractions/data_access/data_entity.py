import abc


class AbstractEntity(abc.ABC):
    """
    Interface for data exchange with database from the side of business instance in python code.

    Methods:

    to_db_dto -- to return suitable db dto (to push into database)

    get_id_str -- to return self id string

    """

    @abc.abstractmethod
    def to_db_dto(self) -> dict:
        pass

    @abc.abstractmethod
    def get_id_str(self) -> str:
        pass
