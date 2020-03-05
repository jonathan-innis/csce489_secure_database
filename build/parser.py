import sys
from lark import Lark, tree, Transformer
from db.database import Database
from db.principal import Principal


# TODO: prog needs to always be starting command
# TODO: fix line 37 38 -> p ???

GRAMMAR = """
start:      auth EOL cmd EOL "***"                            -> start_call

auth:       "as principal " p " password " s " do"          -> auth_call 

cmd:        "exit"                                          -> exit_call                    
            | "return " expr                                -> string_call
            | prim_cmd EOL cmd
            
expr:       value                                           -> string_call                                                                        
            | fieldvals
            
fieldvals:  "x = " value
            | "x = " value ", " fieldvals
            
value:      x                                               -> return_call                                                                                        
            | x "." y                                       -> return_dot_call
            | s                                             -> string_call                                      

prim_cmd:   "create principal " p  pwd                      -> create_principal_call
            | "change password " p pwd                      -> change_password_call
            | "set " x " = " expr                           -> set_call
            | "set " x " = []"                              -> list_set_call
            | "set " x " = [" x "]"                         -> throw_list_error
            | "append to " x " with " expr
            | "local " x " = " expr
            | "foreach " y " in " x " replacewith " expr
            | "set delegation " tgt q right -> p
            | "delete delegation " tgt q right -> p
            | "default delegator = "
            
tgt:        "all"
            | x
            
right:      "read"
            | "write"
            | "append"
            | "delegate"

EOL : " "* ( NEWLINE | /\f/)


p: /[A-Za-z][A-Za-z0-9_]*/                                  -> string_call
pwd: /[A-Za-z][A-Za-z0-9_]*/                                -> string_call
q: /[A-Za-z][A-Za-z0-9_]*/                                  -> string_call
s: /"[A-Za-z0-9_,;\.?!-]*"/                                 -> string_call
x: /[A-Za-z][A-Za-z0-9_]*/                                  -> string_call
y: /[A-Za-z][A-Za-z0-9_]*/                                  -> string_call

%import common.WORD
%import common.WS
%import common.NEWLINE
%ignore WS
"""

class T(Transformer):

    def __init__(self, d):
        self.vars = {}
        self.d = d

    def string_call(self, args):
        return args[0].strip('"')

    def start_call(self, args):
        print(args[0])
        print(args[1])

    def auth_call(self, args):
        p = str(args[0])
        pwd = str(args[1])
        self.d.set_principal(p, pwd)

    def create_principal_call(self, args):
        p = str(args[0])
        pwd = str(args[1])
        self.d.create_principal(p, pwd)

    def change_password_call(self, args):
        p = str(args[0])
        pwd = str(args[1])
        self.d.change_password(p, pwd)

    def exit_call(self, args):
        print("EXITING")

    def value_call(self, args):
        print("value call")

    # strip quotation marks from s strings if necessary
    def set_call(self, args):
        print("set_call")
        key = args[0]
        val = args[1]
        self.d.set_record(key, val)

    def return_call(self, args):
        print("return_call")
        val = str(args[0])
        print(val)
        return self.d.return_record(val)

    def list_set_call(self, args):
        key = str(args[0])
        val = []
        self.d.set_record(key, val)

    def throw_list_error(self, args):
        print("Error: must initialize empty list before adding items")

def main():
    parser = Lark(GRAMMAR)
    d = Database("test")
    text1 = 'as principal admin password "test" do \n set x = "string" \n create principal bobby password \n change password bobby newpassword \n return x \n ***'
    text2 = 'as principal bobby password "newpassword" do \n exit \n ***'
    print(parser.parse(text1).pretty())
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())

    tree1 = parser.parse(text1)
    # print(tree)
    T(d).transform(tree1)

    tree2 = parser.parse(text2)

    T(d).transform(tree2)


if __name__ == '__main__':
    main()
