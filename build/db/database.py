from db.store import Store, RecordKeyError
from db.principal import Principal
from db.permissions import Permissions, Right, ALL_RIGHTS


class PrincipalKeyError(Exception):
    pass


class SecurityViolation(Exception):
    pass


class ParseError(Exception):
    pass


class Database:
    """
    This is the class for the database.

    Attributes:
        - principals ({string: Principal}): Map from the username of the principal to the Principal object.
        - current_principal (Principal): Current principal that has been authenticated and is operating on the database.
        - default_delegator (Principal): Default delegator that rights will be copied from.
        - local_store ({string: [] | {} | string}): Local store to be destroyed after program execution completes.
          Map from the record name to the record itself.
        - global_store ({string: [] | {} | string}): Global store that persists across program executions.
          Map from the record name to the record itself.
        - permissions (Permissions): Data store that keeps track of all of the permissions assignments in the database.
    """

    def __init__(self, admin_password):
        """
        The constructor for the Database class.

        Paramaters:
            admin_password (string): The admin password passed when the database is initialized.

        - Initializes all of the values to have no data in them
        - Creates the admin user and inserts them into the set of principals
        """

        self.__principals = {}
        self.__current_principal = None
        self.__default_delegator = "anyone"
        self.__local_store = Store()
        self.__global_store = Store()
        self.__permissions = Permissions()

        # Creates the admin
        p = Principal("admin", admin_password, admin=True)
        self.__principals["admin"] = p
        p = Principal("anyone", "default", admin=False, accessible=False)
        self.__principals["anyone"] = p

    def get_principal(self, username):
        """
        The function to return a principal from the database.

        Paramaters:
            username (string): The username of the principal

        Returns:
            Principal: Returns the principal with the given username in the database

        Errors:
            PrincipalKeyError(): If username is not in the database.
        """

        if username not in self.__principals:
            raise PrincipalKeyError("username for principal does not exist")
        return self.__principals[username]

    def get_current_principal(self):
        """
        The function to return the current principal from the database.

        Returns:
            Principal: Returns the current principal from the database

        Errors:
            SecurityViolation(): If the current principal is not set
        """
        if not self.__current_principal:
            raise SecurityViolation("current principal is not set")
        return self.__current_principal

    def check_principal_set(self):
        """
        The function is an alias to get_current_principal()

        Errors:
            SecurityViolation(): If the current principal is not set
        """
        self.get_current_principal()

    def create_principal(self, username, password):
        """
        The function to add a new principal to the database

        Parameters:
            username (string): The username of the new principal.
            password (string): The password of the new principal.

        Returns:
            string: Returns "CREATE_PRINCIPAL" if execution completes correctly.

        Errors:
            PrincipalKeyError(): If username already exists in the database
            SecurityViolation(): If current principal creating user isn't admin
        """

        self.check_principal_set()

        if username in self.__principals:
            raise PrincipalKeyError("username for principal exists in database")
        if not self.get_current_principal().is_admin():
            raise SecurityViolation("current principal is not admin user")
        p = Principal(username, password)
        self.__principals[username] = p
        self.set_delegation("all", self.__default_delegator, username, ALL_RIGHTS)

    def set_principal(self, username, password):
        """
        The function to set the principal by authenticating with the given password.

        Parameters:
            username (string): The username of the current principal.
            password (string): The password to authenticate the given principal username.

        Errors:
            SecurityViolation(): If the username does not exist in the database or the given
                                 username password combination does not authenticate correctly.
        """
        if username not in self.__principals:
            raise SecurityViolation("invalid username/password combination for principal")
        p = self.__principals[username]
        if not p.authenticate(password):
            raise SecurityViolation("invalid username/password combination for principal")
        self.__current_principal = p

    def change_password(self, username, password):
        """
        The function to change the password of a principal in the database

        Parameters:
            username (string): The username of the principal whose password we wish to change
            password (string): The new password for the principal.

        Returns:
            string: Returns "CHANGE_PASSWORD" if execution completes correctly.

        Errors:
            SecurityViolation(): If the username specified is not the current principal or the current principal is not admin
            PrincipalKeyError(): If the username specified does not exist in the database.
        """

        self.check_principal_set()

        if username != self.get_current_principal().get_username() and not self.get_current_principal().is_admin():
            raise SecurityViolation("cannot change password of another principal without admin privileges")

        if username == self.get_current_principal().get_username():
            self.get_current_principal().change_password(password)
            self.__principals[username] = self.get_current_principal()
        else:
            if username not in self.__principals:
                raise PrincipalKeyError("username for principal does not exist in the database")
            self.__principals[username].change_password(password)

    def check_permission(self, record_name, right):
        """
        The function to check a given right on the current principal

        Parameters:
            raw_record_name (string): The name of the given record
            right (Right): The record to check on the current principal
        """
        self.check_principal_set()

        return self.__permissions.check_permission(record_name, self.get_current_principal().get_username(), right)

    def set_record(self, record_name, value):
        """
        The function to set a record in either the global store or the local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record

        Returns:
            string: Returns "SET" if execution completes correctly.

        Errors:
            SecurityViolation(): The current principal does not have write permission on an already existing record
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name):
            self.__local_store.set_record(record_name, value)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.WRITE):
                self.__global_store.set_record(record_name, value)
            else:
                raise SecurityViolation("principal does not have write permission on record")
        else:
            self.__global_store.set_record(record_name, value)
            self.__permissions.add_permissions(record_name, "admin", self.get_current_principal().get_username(), ALL_RIGHTS)

    def append_record(self, record_name, value):
        """
        The function to append a value to a record with a given record name in the global or local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record

        Returns:
            string: Returns "APPEND" if execution completes correctly.

        Errors:
            SecurityViolation(): If the current principal does not have write or append permission on the given record name
            RecordKeyError(): If the record name does not exist in the local or global store
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name):
            self.__local_store.append_record(record_name, value)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.WRITE) or self.check_permission(record_name, Right.APPEND):
                self.__global_store.append_record(record_name, value)
            else:
                raise SecurityViolation("principal does not have write permission or append permission on record")
        else:
            raise RecordKeyError("record does not exist in the database")

    def set_local_record(self, record_name, value):
        """
        The function to store a local record with the given record name in the local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record

        Returns:
            string: Returns "LOCAL" if execution completes correctly.

        Errors:
            RecordKeyError(): If the given record name already exists in the local or global store
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name) or self.__global_store.read_record(record_name):
            raise RecordKeyError("record name already exits in the database")
        else:
            self.__local_store.set_record(record_name, value)

    def return_record(self, record_name):
        """
        The function to return a record either from the global store or the local store

        Parameters:
            record_name (string): The name of the record

        Returns:
            (string | dict | list): The value associated with the record

        Errors:
            SecurityViolation(): If the principal does not have write permissions on the record
            RecordKeyError(): If the record does not exist in the database
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name):
            return self.__local_store.read_record(record_name)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.READ):
                return self.__global_store.read_record(record_name)
            else:
                raise SecurityViolation("principal does not have read permission on record")
        else:
            raise RecordKeyError("record does not exist in the database")

    def set_delegation(self, tgt, from_principal, to_principal, right):
        """
        The function to delegate a given right from a principal to another principal on a target

        Parameters:
            tgt (string): The target that we want to assign rights to (record_name or "all")
            from_principal (string): Principal username that delegates the right
            right (Right): The type of right that is being delegated
            to_principal (string): Principal username that has the right delegated to them
        
        Errors:
            SecurityViolation(): 
                - If the from_principal is not the current principal or admin
                - If the principal does not have delegate permission on X and isn't admin
            RecordKeyError(): If the record name does not exist in the global store
        """

        self.check_principal_set()

        self.get_principal(from_principal) #This performs a check to see if the from_principal exists
        self.get_principal(to_principal) #This performs a check to see if the to_principal exists

        # If current principal is not from_principal or admin, throw an error
        curr_username = self.get_current_principal().get_username()
        if from_principal != curr_username and curr_username != "admin":
            raise SecurityViolation("principal specified is not current principal or admin")
        
        # Iterates through the elements that a user has delegate rights on
        if tgt == 'all':
            from_rights = self.__permissions.return_permission_keys(from_principal)
            for elem in from_rights:
                # Checking whether the principal has delegate permission on object and element exists in global store
                if self.__permissions.check_permission(elem, from_principal, Right.DELEGATE) and self.__global_store.read_record(elem):
                    self.__permissions.add_permissions(elem, from_principal, to_principal, right)
        else:
            # Checking whether if the current user is not an admin user, if the from principal has delegate permissions
            if curr_username != "admin" and not self.__permissions.check_permission(tgt, from_principal, Right.DELEGATE):
                raise SecurityViolation("principal specified does not have permissions to delegate")
            elif not self.__global_store.read_record(tgt):
                raise RecordKeyError("record does not exist in the global store")
            self.__permissions.add_permissions(tgt, from_principal, to_principal, right)

    def delete_delegation(self, tgt, from_principal, to_principal, right):

        self.check_principal_set()

        self.get_principal(from_principal) #This performs a check to see if the from_principal exists
        self.get_principal(to_principal) #This performs a check to see if the to_principal exists

        # If current principal is not from_principal, to_principal, or admin, throw error
        curr_username = self.get_current_principal().get_username()
        if curr_username != from_principal and curr_username != to_principal and curr_username != "admin":
            raise SecurityViolation("principal specified is not current principal or admin")

        # Iterates through the elements that a user has delegate rights on
        if tgt == 'all':
            from_rights = self.__permissions.return_permission_keys(from_principal)
            for elem in from_rights:
                # Checking whether the principal has delegate permission on object and element exists in global store
                if self.__permissions.check_permission(elem, from_principal, Right.DELEGATE) and self.__global_store.read_record(elem):
                    self.__permissions.delete_permission(elem, from_principal, to_principal, right)
        else:
            if curr_username != "admin" and not self.__permissions.check_permission(tgt, from_principal, Right.DELEGATE):
                raise SecurityViolation("principal specified does not have permissions to delegate")
            elif not self.__global_store.read_record(tgt):
                raise RecordKeyError("record does not exist in the global store")
            self.__permissions.delete_permission(tgt, from_principal, to_principal, right)

    def set_default_delegator(self, username):

        self.check_principal_set()

        if username not in self.__principals:
            raise PrincipalKeyError("username for principal does not exist in database")
        if not self.get_current_principal().is_admin():
            raise SecurityViolation("current principal is not admin user")
        self.__default_delegator = username

    def exit(self):
        """
        The function to exit from the database and reset the local variables in the database
        """
        self.check_principal_set()

        self.__current_principal = None
        self.__local_store = Store()