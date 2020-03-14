from db.database import *
from parse.parser import *

d = Database("admin")
p = Parser()
p.parse(d, 'as principal admin password "admin" do\ncreate principal bob "password1"\ncreate principal alice "password2"\ncreate principal eve "password3"\nreturn "exiting"\n***')