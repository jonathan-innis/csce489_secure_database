# Secure Database
Clients can connect to the server via TCP and send a textual program, which is a list of commands whose grammar is given below. The server executes the program, sends textual output back to the client, and disconnects. Executing a program may cause data to be stored on the server, which can be accessed later by other programs. The server accepts one connection at a time (so programs never execute concurrently).

## Database Schema

```
{
  "key": {
    "data": <value>,
    "read": [Principal],
    "write": [Principal],
    "append": [Principal],
    "delegate": [Principal]
   }
}
```

## Principal File Schema

```
{
  "username": <string>,
  "password": hash(<string>),
}
```
