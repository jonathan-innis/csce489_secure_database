from store import Store

class Database:
    def __init__(self):
        self.principals = {}
        self.default_delegator = None
        self.local_store = Store()
        self.global_store = Store()
    
    def create_principal(self, username, password):
        p = Principal(username, password, self.default_delegator)
        self.principals[username] = p
