import abc


class Exchangeable(abc.ABC):
    """
    Classes wich are implements that interface can be converted into the dictionary object like DTO to serialisation process by executing the to_dto method

    """

    @abc.abstractmethod
    def to_web_dto(self) -> dict:
        pass

    @abc.abstractmethod
    def from_web_dto(dto: dict) -> object:
        pass
