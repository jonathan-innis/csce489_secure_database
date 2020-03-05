import sys
from lark import Lark, tree, Transformer
from database import Database
from principal import Principal


# TODO: prog needs to always be starting command
# TODO: fix line 37 38 -> p ???

GRAMMAR = """
start:    prog 

prog:       "as principal " p " password " pwd " do " cmd   -> prog_call 

cmd:        "exit"                                          -> exit_call                    
            | "return " expr                                -> return_call
            | prim_cmd
            
expr:       value                                                                             
            | fieldvals
            
fieldvals:  "x = " value
            | "x = " value ", " fieldvals
            
value:      x                                                                                             
            | x "." y
            | s                                                                                  

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
            | "default delegator = " p
            
tgt:        "all"
            | x
            
right:      "read"
            | "write"
            | "append"
            | "delegate"

p: WORD     
pwd: WORD
q: WORD
s: /"[A-Za-z0-9_,;\.?!-]*"/
x: /[A-Za-z][A-Za-z0-9_]*/
y: WORD  


%import common.WORD
%import common.WS
%ignore WS
"""

class T(Transformer):

    def __init__(self):
        self.vars = {}
        self.d = Database('pass')
        self.d.set_principal('admin', 'pass')

    def prog_call(self, args):
        p = str(args[0].children[0])
        pwd = str(args[1].children[0])
        # self.d.set_principal(p, pwd)

    def create_principal_call(self, args):
        p = str(args[0].children[0])
        pwd = str(args[1].children[0])
        self.d.create_principal(p, pwd)

    def change_password_call(self, args):
        p = str(args[0].children[0])
        pwd = str(args[1].children[0])
        self.d.change_password(p, pwd)

    def exit_call(self, args):
        print("EXITING")

    def value_call(self, args):
        print("value call")

    def x_call(self, args):
        print("x_call")
        val = str(args[0].children[0])
        # self.d.return_record(x)

    # strip quotation marks from s strings if necessary
    def set_call(self, args):
        print("set_call")
        key = str(args[0].children[0])
        val = str(args[1].children[0].children[0].children[0])
        val = val.strip('"')
        self.d.set_record(key, val)

    def return_call(self, args):
        print("return_call")
        val = str(args[0].children[0].children[0].children[0])
        print(val)
        # self.d.return_record(val)

    def list_set_call(self, args):
        key = str(args[0].children[0])
        val = str("[]")
        self.d.set_record(key, val)

    def throw_list_error(self, args):
        print("Error: must initialize empty list before adding items")

def main():
    parser = Lark(GRAMMAR)
    text1 = "as principal pal password key do "
    text2 = "set x = []"
    text = text1 + text2
    print(text)
    print(parser.parse(text).pretty())
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())

    tree = parser.parse(text)
    # print(tree)
    print(T().transform(tree))


if __name__ == '__main__':
    main()
