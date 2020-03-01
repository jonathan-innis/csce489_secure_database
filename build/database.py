from build.store import Store, RecordKeyError
from build.principal import Principal
from build.permissions import Permissions, Right, ALL_RIGHTS


class PrincipalKeyError(Exception):
    pass


class SecurityViolation(Exception):
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
        self.__default_delegator = None
        self.__local_store = Store()
        self.__global_store = Store()
        self.__permissions = Permissions()

        # Creates the admin
        p = Principal("admin", admin_password, admin=True)
        self.__principals["admin"] = p

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
        p = Principal(username, password, self.__default_delegator)
        self.__principals[username] = p

        return "CREATE_PRINCIPAL"

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

        return "CHANGE_PASSWORD"

    def check_permission(self, record_name, right):
        """
        The function to check a given right on the current principal

        Parameters:
            raw_record_name (string): The name of the given record
            right (Right): The record to check on the current principal
        """
        return self.__permissions.check_permission(record_name, self.get_current_principal().get_username(), right)

    def set_record(self, record_name, expr, is_ref=False):
        """
        The function to set a record in either the global store or the local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record
            is_ref (bool): Whether the element is a literal value or a reference

        Returns:
            string: Returns "SET" if execution completes correctly.

        Errors:
            SecurityViolation(): The current principal does not have write permission on an already existing record
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name):
            if is_ref:
                expr = self.return_record(expr) # Pulls the referenced variable from the database
            self.__local_store.set_record(record_name, expr)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.WRITE):
                if is_ref:
                    expr = self.return_record(expr) # Pulls the referenced variable from the database
                self.__global_store.set_record(record_name, expr)
            else:
                raise SecurityViolation("principal does not have write permission on record")
        else:
            if is_ref:
                expr = self.return_record(expr) # Pulls the referenced variable from the database
            self.__global_store.set_record(record_name, expr)
            self.__permissions.add_permissions(record_name, "admin", self.get_current_principal().get_username(), ALL_RIGHTS)

        return "SET"

    def append_record(self, record_name, expr, is_ref=False):
        """
        The function to append a value to a record with a given record name in the global or local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record
            is_ref (bool): Whether the element is a literal value or a reference

        Returns:
            string: Returns "APPEND" if execution completes correctly.

        Errors:
            SecurityViolation(): If the current principal does not have write or append permission on the given record name
            RecordKeyError(): If the record name does not exist in the local or global store
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name):
            if is_ref:
                expr = self.return_record(expr)
            self.__local_store.append_record(record_name, expr)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.WRITE) or self.check_permission(record_name, Right.APPEND):
                if is_ref:
                    expr = self.return_record(expr)
                self.__global_store.append_record(record_name, expr)
            else:
                raise SecurityViolation("principal does not have write permission or append permission on record")
        else:
            raise RecordKeyError("record does not exist in the database")

        return "APPEND"

    def set_local_record(self, record_name, expr, is_ref=False):
        """
        The function to store a local record with the given record name in the local store

        Parameters:
            record_name (string): The name of the record
            expr (string | dict | list): The value or reference to be appended to the record
            is_ref (bool): Whether the element is a literal value or a reference

        Returns:
            string: Returns "LOCAL" if execution completes correctly.

        Errors:
            RecordKeyError(): If the given record name already exists in the local or global store
        """

        self.check_principal_set()

        if self.__local_store.read_record(record_name) or self.__global_store.read_record(record_name):
            raise RecordKeyError("record name already exits in the database")
        else:
            if is_ref:
                expr = self.return_record(expr)
            self.__local_store.set_record(record_name, expr)

        return "LOCAL"

    def for_each(self, local_var, record_name, expr, is_ref=False):
        """
        The function to iterate over a given record with a local variable and evaluate each part of the list
        wth an expression and then replace that element with the result of that experssion

        Parameters:
            local_var (string): The name of the local variable
            record_name (string): The name of the record
            expr (function): The function to execute on each part of the record

        Errors:
            RecordKeyError(): The local variable name already exists in the database or the record_name does not exist in the database
            SecurityVioloation(): The principal does not have permissions to both read and write the record
        """

        self.check_principal_set()

        if self.__local_store.read_record(local_var) or self.__global_store.read_record(local_var):
            raise RecordKeyError("local variable name already exists in the database")

        if self.__local_store.read_record(record_name):
            self.__local_store.for_each_record(record_name, local_var, expr, is_ref)
        elif self.__global_store.read_record(record_name):
            if self.check_permission(record_name, Right.READ) and self.check_permission(record_name, Right.WRITE):
                self.__global_store.for_each_record(record_name, local_var, expr, is_ref)
            else:
                raise SecurityViolation("principal does not have both read and write permission on record")
        else:
            raise RecordKeyError("record name does not exist in the database")

        return "FOREACH"
        

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

    def exit(self):
        """
        The function to exit from the database and reset the local variables in the database
        """

        self.__current_principal = None
        self.__local_store = Store()
