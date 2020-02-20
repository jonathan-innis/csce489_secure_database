class Database:
    def __init__(self):
        self.principals = {}
        self.default_delegator = Principal
        self.local_store = Store
        self.global_store = Store
