from db.database import Database
from parser.parser import parse

d = Database("admin")
text = 'as       principal admin password "admin" do\ncreate principal bob "BOBPWxxd"\nset x="my string"\nset y = { f1     = x   , f2    =    "field2" }\nset delegation x admin read -> bob\nreturn y.f1\n***'

ret = parse(d, text)
print(ret)