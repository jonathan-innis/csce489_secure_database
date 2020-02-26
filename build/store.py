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

    def deepcopy_record(self, value):
        """
        The function to deepcopy a record so that the original is not altered

        Parameters:
            value (string | dict | list): The value associated with a record
        
        Returns:
            value (string | dict | list): The copy of the given value
        """

        if isinstance(value, dict):
            return dict(value)
        elif isinstance(value, list):
            return value[:]
        elif isinstance(value, str):
            return value
        else:
            return None

    def append_to_record(self):
        pass

    def read_record(self, record_name):
        """
        The function to read a record from the store

        Parameters:
            record_name (string): The name of the record
        
        Returns:
            value (string | dict | list): A deepcopy of the original record
        """

        return self.deepcopy_record(self.__store.get(record_name, None))

    def for_each_record(self):
        pass
