import copy


class AppendException(Exception):
    pass


class ForEachException(Exception): 
    pass


class RecordKeyError(Exception):
    pass


class Store:
    """
    This is the class for stores in the database

    Attributes:
        store (dict({string: string | dict | list)): The records stored in the database
    """
    def __init__(self):
        self.__store = {} 

    def set_record(self, record_name, expr, is_ref=False):
        """
        The function to set the record with the given name to the given value.

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference associated with the record
            is_ref (bool): Whether the element is a literal value or a reference
        """

        #Checking if the element is a reference and reading the record if it is
        if is_ref:
            expr = self.read_record(expr)
        self.__store[record_name] = expr

    def append_record(self, record_name, expr, is_ref=False):
        """
        The function to append the record with the given name with the given value.

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record
            is_ref (bool): Whether the element is a literal value or a reference

        Errors:
            AppendException(): If the value associated with the record name is not a list
        """

        record = self.__store[record_name]

        # Checking if the element is a reference and reading the record if it is
        if is_ref:
            expr = self.read_record(expr)

        if not isinstance(record, list):
            raise AppendException("unable to append record to non-list object")
        else:
            if isinstance(expr, list):
                record += expr
            else:
                record.append(expr)
        self.__store[record_name] = record

    def read_record(self, record_name):
        """
        The function to read a record from the store. Recursively reads the record
        from the database reading each of the dots in the reference

        Parameters:
            record_name (string): The name of the record

        Returns:
            value (string | dict | list | None): A deepcopy of the original record
        """

        print(self.__store)

        record = self.__store
        for elem in record_name.split('.'):
            if elem not in record:
                return None
            record = record[elem]
        return copy.deepcopy(record)

    def delete_record(self, record_name):
        """
        The function to delete the record from the store. Recursively reads the record
        from the database reading each of the dots of the reference

        Parameters:
            record_name (string): The name of the record

        Errors:
            RecordKeyError(): If the record does not exist in the store
        """

        record = self.__store
        split_record_name = record_name.split('.')
        for i in range(len(split_record_name) - 1):
            if split_record_name[i] not in record:
                return RecordKeyError("record not in database")
            record = record[split_record_name[i]]
        
        del record[split_record_name[-1]]

    def for_each_record(self, record_name, local_var, expr, is_ref=False):
        """
        The function to iterate over a record name and execute a given expression on each element

        Parameters:
            record_name (string): The name of the record
            expr (function): The function to execute on each part of the record
        
        Errors:
            ForEachException(): If the record with the given record name is not a list or the 
                expression function evaluates to a list on a given element
        """

        record = []
        list_record = self.read_record(record_name)

        if not isinstance(list_record, list):
            raise ForEachException("unable to iterate through non-list object") 

        for i, elem in enumerate(list_record):
            self.set_record(local_var, elem)
            
            updated_record = expr
            if is_ref:
                updated_record = self.read_record(expr)

            if isinstance(updated_record, list):
                raise ForEachException("expression evaluates to list object")
            record.append(updated_record)
            
        self.set_record(record_name, record)
        self.delete_record(local_var)
