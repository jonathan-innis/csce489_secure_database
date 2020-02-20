from store import Store

class Database:
    def __init__(self):
        self.principals = {}
        self.default_delegator = None
        self.local_store = Store()
        self.global_store = Store()
