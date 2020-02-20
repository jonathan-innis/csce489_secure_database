import hashlib

class Principal:
    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.sha256(password)
        self.local_permissions = {}
        self.global_permissions = {}
    
    def authenticate(self, password):
        if hashlib.sha256(password) == self.password:
            return True
        return False

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
