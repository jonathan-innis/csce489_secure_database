import copy


class AppendException(Exception):
    pass


class Store:
    """
    This is the class for stores in the database

    Attributes:
        store (dict({string: string | dict | list)): The records stored in the database
    """
    def __init__(self):
        self.__store = {}

    def set_record(self, record_name, value):
        """
        The function to set the record with the given name to the given value.

        Parameters:
            record_name (string): The name of the record
            value (string | dict | list): The value associated with the record
        """

        self.__store[record_name] = value

    def append_record(self, record_name, value):
        """
        The function to append the record with the given name with the given value.

        Parameters:
            record_name (string): The name of the record
            value (string | dict | list): The value to be appended to the record
        
        Errors:
            AppendException(): If the value associated with the record name is not a list
        """

        record = self.__store[record_name]
        if not isinstance(record, list):
            raise AppendException("unable to append record to non-list object")
        else:
            if isinstance(value, list):
                record += value
            else:
                record.append(value)
        self.__store[record_name] = record        

    def read_record(self, record_name):
        """
        The function to read a record from the store

        Parameters:
            record_name (string): The name of the record

        Returns:
            value (string | dict | list): A deepcopy of the original record
        """

        return copy.deepcopy(self.__store.get(record_name, None))

    def for_each_record(self):
        pass
