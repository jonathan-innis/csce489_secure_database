from db.permissions import Right


class Cache:
    
    def __init__(self):
        self.__data = {}
    
    def check(self, record_name, right):
        if right in self.__data.get(record_name, dict()):
            return True
        return False

    def update(self, record_name, right):
        if record_name not in self.__data:
            self.__data[record_name] = set()
        self.__data[record_name].add(right)

    def reset(self, record_name, right):
        self.__data.get(record_name, set()).discard(right)
