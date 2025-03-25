import abstractions.data_access.data_entity as de, abc


class Repository(abc.ABC):
    """
    Interface for data exchange with database from the side of repository in python code.

    Methods:

    create -- for create an instance in database by the example of target instance from parameters;

    update -- for update a db instance from changes in python instance;

    delete -- to delete persistent instance on the side of db;

    delete -- to delete persistent instance on the side of db with such id;

    find_all_by_ids -- to find all instances with such ids and return a list of them

    """

    @abc.abstractmethod
    def create(self, entity: de.AbstractEntity):
        pass

    @abc.abstractmethod
    def update(self, entity: de.AbstractEntity):
        pass

    @abc.abstractmethod
    def delete(self, entity: de.AbstractEntity):
        pass

    @abc.abstractmethod
    def delete_by_id(self, id):
        pass

    @abc.abstractmethod
    def find_all_by_ids(self, ids: list) -> list:
        pass

    @abc.abstractmethod
    def find_by_id(self, id) -> dict:
        pass

    @abc.abstractmethod
    def find_all_by_page(self, from_id, page_size: int) -> dict:
        pass
