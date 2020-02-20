import hashlib

class Principal:
    def __init__(self, username, password, default_delegator = None):
        self.username = username
        self.password = hashlib.sha256(password)

        if default_delegator is None:
            self.local_permissions = {}
            self.global_permissions = {}
        else:
            self.local_permissions = dict(default_delegator.local_permissions)
            self.global_permissions = dict(default_delegator.global_permissions)

    def authenticate(self, password):
        if hashlib.sha256(password) == self.password:
            return True
        return False

    def change_password(self, new_password):
        self.password = hashlib.sha256(new_password)

    def add_local_permission():
        pass

    def delete_local_permission():
        pass
    
    def add_global_permission():
        pass

    def delete_global_permission():
        pass

    def check_permission():
        pass
