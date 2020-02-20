class Principal:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.local_permissions = {}
        self.global_permissions = {}
    
    def authenticate(self):
        pass
