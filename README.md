# Secure Database
Clients can connect to the server via TCP and send a textual program, which is a list of commands whose grammar is given below. The server executes the program, sends textual output back to the client, and disconnects. Executing a program may cause data to be stored on the server, which can be accessed later by other programs. The server accepts one connection at a time (so programs never execute concurrently).

## Class Schema

### Database
```python
class Database:

  def __init__(self):
    self.principals = {"name": Principal}
    self.default_delegator = Principal
    self.local_store = Store
    self.global_store = Store
    
  def build_from_file(self):
    pass
    
  def write_to_file(self):
    pass
  
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
    self.password = hash(password)
    self.local_permissions = {"record_name": ["permission"]}
    self.global_permissions = {"record_name": ["permission"]}
    
  def authenticate(self):
    pass
```

## Output Schema

```json
{
  "status": "status_message",
  "output": "<value>"
}
