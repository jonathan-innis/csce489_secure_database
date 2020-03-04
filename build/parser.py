import sys
from lark import Lark, tree, Transformer
from database import Database
from principal import Principal

# TODO: replace WORD instances with proper regex definition
# TODO: fix line 37 38 -> p ???

GRAMMAR = """
start:    prog 
        | cmd
        | expr
        | fieldvals
        | value
        | prim_cmd
        |tgt
        | right

prog:       "as principal " p " password " pwd  -> prog

cmd:        "exit"                              -> exit
            | "return " expr 
            | prim_cmd
            
expr:       value 
            | "[]"
            | fieldvals
            
fieldvals:  "x = " value
            | "x = " value "," fieldvals
            
value:      x 
            | x "." y
            | s
            
prim_cmd:   "create principal " p
            | "change password " pwd
            | "set x = " expr
            | "append to x with " expr
            | "local x = " expr
            | "foreach y in x replacewith " expr
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
s: WORD
x: /[A-Za-z][A-Za-z0-9]/
y: /[A-Za-z][A-Za-z0-9]/

%import common.WORD
%import common.WS
%ignore WS
"""

class T(Transformer):

    def __init__(self):
        self.vars = {}
        self.d = Database('pass')
        self.d.set_principal('admin', 'pass')

    def prog(self, args):
        p = str(args[0].children[0])
        pwd = str(args[1].children[0])
        self.d.create_principal(p, pwd)
        print("prog calls create_principal")

    def exit(self, args):
        print("EXITING")

    def value(self, args):
        print("value")



def main():
    parser = Lark(GRAMMAR)
    text = "as principal pal password key"
    print(parser.parse(text).pretty())
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())

    tree = parser.parse(text)
    print(tree)
    print(T().transform(tree))


if __name__ == '__main__':
    main()
