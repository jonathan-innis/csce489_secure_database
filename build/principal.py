import bcrypt

class Principal:
    """
    This is the class for principals in the database

    Attributes:
        username (string): The username of the principal. 
        salt (byte_string): The salt to use when hashing a principal's password.
        password (byte_string): The stored hashed password.
        is_admin (bool): Whether the user has admin privileges or not.
    """

    def __init__(self, username, password, default_delegator = None):
        """
        The constructor for Principal class.

        Paramateers:
            username (string): The username of the principal.
            password (string): The password of the principal.
            default_delegator (Principal): The default delegator to have rights copied from.

        - Sets the username of the principal
        - Generates a new salt for the password and hashes the password with this salt
        - Sets the admin rights to false
        - Copies all of the permissions from the default delegator
        """

        self.username = username
        self.salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode('utf-8'), self.salt)
        self.is_admin = False

        if default_delegator is None:
            self.local_permissions = {}
            self.global_permissions = {}
        else:
            self.local_permissions = dict(default_delegator.local_permissions)
            self.global_permissions = dict(default_delegator.global_permissions)

    def authenticate(self, password):
        """
        The function to authenticate a user given a password.

        Parameters:
            password (string): The password to compare to the current stored password

        Returns:
            bool: Whether the given password authenticates the user correctly.
        """

        if bcrypt.checkpw(password.encode('utf-8'), self.password):
            return True
        return False

    def change_password(self, new_password):
        """
        The function to generate a new salt for the new password and 
        hash the new password with this salt

        Parameters:
            new_password (string): The new password for the principal
        """

        self.salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(new_password.encode('utf-8'), self.salt)

    def add_local_permission(item, permission):
        pass

    def delete_local_permission():
        pass
    
    def add_global_permission():
        pass

    def delete_global_permission():
        pass

    def check_permission():
        pass