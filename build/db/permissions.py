from enum import Enum
from collections import deque


class PermissionsKeyError(Exception):
    pass


class Right(Enum):
    WRITE = 1
    READ = 2
    APPEND = 3
    DELEGATE = 4


ALL_RIGHTS = [Right.WRITE, Right.READ, Right.APPEND, Right.DELEGATE]


class Permissions:
    """
    This is the class for principal permissions in the database

    Attributes:
        data (dict): The data store for principal permissions
    """

    def __init__(self):
        """
        The constructor for Permissions class.

        - Initializes the data store to an empty dictionary.
        """

        self.__data = dict()
    
    def add_permissions(self, record_name, from_principal, to_principal, rights):
        """
        The function to add a mapping that a principal gives a set of rights to another principal.

        Parameters:
            record_name (string): The name of the given record
            from_principal (string): The username of the principal giving rights.
            to_principal (string): The username of the principal receiving rights.
            rights ([Right]): A list of rights to give to the principal. 
        """

        if to_principal not in self.__data:
            self.__data[to_principal] = dict()
        if record_name not in self.__data[to_principal]:
            self.__data[to_principal][record_name] = dict()
        
        if isinstance(rights, list):
            for right in rights:
                if right not in self.__data[to_principal][record_name]:
                    self.__data[to_principal][record_name][right] = set()
                self.__data[to_principal][record_name][right].add(from_principal)
        elif isinstance(rights, Right):
            if rights not in self.__data[to_principal][record_name]:
                self.__data[to_principal][record_name][rights] = set()
            self.__data[to_principal][record_name][rights].add(from_principal)
        else:
            raise PermissionsKeyError("right type does not exist")

    def check_permission(self, record_name, principal, right):
        """
        The function to check whether a principal name has a right given through transitivity.
        - If a user receives rights that trace back to an admin or to the pseudo-user: anyone,
          that user has rights on the record.
        
        ex: user2 -> user1 -> admin

        Parameters:
            record_name (string): The name of the given record
            principal (string): The username of the principal to check rights.
            right (Right): The given right to check on the given principal.

        Returns:
            bool: Whether a given user has a permission on the given record
        """

        if principal == "admin":
            return True
        if self.check_permission_helper(record_name, "anyone", right):
            return True
        if self.check_permission_helper(record_name, principal, right):
            return True
        return False

    def check_permission_helper(self, record_name, principal, right):
        visited = set()
        q = deque()

        q.append(principal)
        visited.add(principal)

        # Doing a BFS to check permissions and ensure that permission have been passed on correctly
        while q:
            s = q.popleft()

            delegators = self.__data.get(s, dict()).get(record_name, dict()).get(right, None)

            if delegators:
                for delegator in delegators:
                    if delegator == "admin":
                        return True
                    if delegator not in visited:
                        q.append(delegator)
                        visited.add(delegator)
        return False

    def return_permission_keys(self, principal):
        """
        Return all records which the principal has any right on
        """
        return self.__data.get(principal, dict()).keys()

    def delete_permission(self, record_name, from_principal, to_principal, right):
        """
        The function to delete a given right delegation from one principal to another

        Parameters:
            record_name (string): The name of the given record
            from_principal (string): The username of the principal giving rights.
            to_principal (string): The username of the principal receiving rights.
            right (Right): The right to remove from the delegation.
        """

        if to_principal not in self.__data:
            return
        if record_name not in self.__data[to_principal]:
            return
        if right not in self.__data[to_principal][record_name]:
            return
        self.__data[to_principal][record_name][right].discard(from_principal)

        # Removing permissions from the system if the elements of the permissions object is empty
        if len(self.__data[to_principal][record_name][right]) == 0:
            del self.__data[to_principal][record_name][right]
        if len(self.__data[to_principal][record_name]) == 0:
            del self.__data[to_principal][record_name]
        if len(self.__data[to_principal]) == 0:
            del self.__data[to_principal]
