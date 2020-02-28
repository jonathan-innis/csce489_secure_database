import bcrypt
import copy
from enum import Enum


class Permission(Enum):
    WRITE = 1
    READ = 2
    APPEND = 3
    DELEGATE = 4


ALL_PERMISSIONS = (Permission.WRITE, Permission.READ, Permission.APPEND, Permission.DELEGATE)


class PermissionsKeyError(Exception):
    pass


class Principal:
    """
    This is the class for principals in the database

    Attributes:
        username (string): The username of the principal.
        salt (byte_string): The salt to use when hashing a principal's password.
        password (byte_string): The stored hashed password.
        is_admin (bool): Whether the user has admin privileges or not.
    """

    def __init__(self, username, password, admin=False, default_delegator=None):
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

        self.__username = username
        self.__salt = bcrypt.gensalt()
        self.__password = bcrypt.hashpw(password.encode('utf-8'), self.__salt)
        self.__admin = admin
        self.__permissions = {}

        if default_delegator:
            self.__permissions = copy.deepcopy(default_delegator.get_permissions())

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

    def get_permissions(self):
        """
        The getter function for permissions.

        Returns:
            dict({string: set(Permission)}): List of user's permissions
        """

        return self.__permissions

    def authenticate(self, password):
        """
        The function to authenticate a user given a password.

        Parameters:
            password (string): The password to compare to the current stored password

        Returns:
            bool: Whether the given password authenticates the user correctly.
        """

        if bcrypt.checkpw(password.encode('utf-8'), self.__password):
            return True
        return False

    def change_password(self, new_password):
        """
        The function to generate a new salt for the new password and
        hash the new password with this salt

        Parameters:
            new_password (string): The new password for the principal
        """

        self.__salt = bcrypt.gensalt()
        self.__password = bcrypt.hashpw(new_password.encode('utf-8'), self.__salt)

    def add_permissions(self, record_name, permissions):
        """
        The function to add the given permissions to the record with the
        given record name

        Parameters:
            record_name (string): The name of the record
            permissions ([Permission]): A list of permissions
        """

        split_record_name = record_name.split('.')
        principal_permissions = self.__permissions.get(split_record_name[0], set())
        for permission in permissions:
            principal_permissions.add(permission)
        self.__permissions[record_name] = principal_permissions

    def has_permission(self, record_name, permission):
        """
        The function to check if a user has the given permission on the
        given record with the record name

        Parameters:
            record_name (string): The name of the record
            permission (Permission): The type of the permission

        Returns:
            bool: If the user has given permission on the record
        """

        split_record_name = record_name.split('.')
        return permission in self.__permissions.get(split_record_name[0], set())

    def delete_permission(self, record_name, permission):
        """
        The function to delete a permission from a given record

        Paramaters:
            record_name (string): The name of the record
            permission (Permission): The type of the permission
        """

        split_record_name = record_name.split('.')
        self.__permissions[split_record_name[0]].discard(permission)
