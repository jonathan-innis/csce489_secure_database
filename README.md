# Secure Database
Clients can connect to the server via TCP and send a textual program, which is a list of commands whose grammar is given below. The server executes the program, sends textual output back to the client, and disconnects. Executing a program may cause data to be stored on the server, which can be accessed later by other programs. The server accepts one connection at a time (so programs never execute concurrently).

## Unit Testing
Testing will be done with the **Pytest** packages. This can be installed by running the following:
```
pip install pytest
```
Unit tests must completely pass for code to be merged in. Tests can be run with the following from the root directory:
```
pytest build/
```

## Linter
Linting will be done with the **Flake8** package. This can be installed by running the following:
```
pip install flake8
```
Linting will be done to check warnings and undefined definitions with the following commands from the root directory:
```
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```
Warnings will be treated as errors for linting purposes.

## Program Execution
When programs execute, they will create a temporary version of the database so that any changes that are invalid can be rolled back to the old version of the database. If changes are valid to completion of the program, the temporary `Database` replaces the older version of the database.

## Local Variables
Local variables will be destroyed from the local store when the program completes execution. Any local permssions from principals will also be destoryed.

## Class Schema

### Database
```python
class Database:
    def __init__(self):
        self.principals = {"name": Principal}
        self.default_delegator = Principal
        self.local_store = Store
        self.global_store = Store
  
```

### Store 
```python
class Store:
    def __init__(self):
        self.store = {"record_name": "<value>"}
    
    def set_record(self):
        pass
    
    def append_record(self):
        pass
        
    def read_record(self):
        pass
    
    def for_each_record(self):
        pass
    
    def change_permissions(self):
        pass
    
    def delete_permissions(self):
        pass
```

### Principal
```python
class Principal:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.local_permissions = {}
        self.global_permissions = {}
    
    def authenticate(self, password):
        pass

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
```

## Output Schema

```json
{
    "status": "status_message",
    "output": "<value>"
}
