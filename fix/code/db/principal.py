import hashlib
import copy


class Principal:
    """
    This is the class for principals in the database

    Attributes:
        username (string): The username of the principal.
        salt (byte_string): The salt to use when hashing a principal's password.
        password (byte_string): The stored hashed password.
        is_admin (bool): Whether the user has admin privileges or not.
    """

    def __init__(self, username, password, admin=False):
        """
        The constructor for Principal class.

        Paramaters:
            username (string): The username of the principal.
            password (string): The password of the principal.
            admin (bool): Whether the user is an admin or not.

        - Sets the username of the principal
        - Generates a new salt for the password and hashes the password with this salt
        - Sets the admin rights to false
        - Copies all of the permissions from the default delegator
        """

        self.__username = username
        if password is None:
            self.__password = None
        else:
            self.__password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.__admin = admin

    def get_username(self):
        """
        The getter function for username.

        Returns:
            string: Username of the principal
        """

        return self.__username

    def is_admin(self):
        """
        The getter function for admin.

        Returns:
            bool: Whether the user is an admin
        """

        return self.__admin

    def authenticate(self, password):
        """
        The function to authenticate a user given a password.

        Parameters:
            password (string): The password to compare to the current stored password

        Returns:
            bool: Whether the given password authenticates the user correctly.
        """

        # If principal is not accessible, deny access
        if self.__password is None:
            return False

        if hashlib.sha256(password.encode('utf-8')).hexdigest() == self.__password:
            return True
        return False

    def change_password(self, new_password):
        """
        The function to generate a new salt for the new password and
        hash the new password with this salt

        Parameters:
            new_password (string): The new password for the principal
        """

        self.__password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        return True
