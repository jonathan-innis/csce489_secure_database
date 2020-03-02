import sys
from lark import Lark, tree

# TODO: replace WORD instances with proper regex definition

GRAMMAR = """
start:    prog
        | cmd
        | expr
        | fieldvals
        | value
        | prim_cmd
        |tgt
        | right


prog: "as principal " p " password " pwd
p: WORD     
pwd: WORD
cmd: "exit"\n
    | "return " expr\n
    | prim_cmd\n
expr: value
    | "[]"
    | fieldvals
fieldvals:    "x = " value
            | "x = " value "," fieldvals
value:    "x"
        | "x*y"
        | s
s: WORD
prim_cmd: "create principal " p
        | "change password " pwd
        | "set x = " expr
        | "append to x with " expr
        | "local x = " expr
        | "foreach y in x replacewith " expr
        | "set delegation " tgt q right -> p
        | "delete delegation " tgt q right -> p
        | "default delegator = " p
tgt: "all"
    | "x"
right: "read"
     | "write"
     | "append"
     | "delegate"
q: WORD

%import common.WORD
"""


def main():
    parser = Lark(GRAMMAR)
    print(parser.parse("as principal pal password key"))
    print(parser.parse("exit"))  # test cmd
    print(parser.parse("create principal prince"))  # test prim cmd
    print(parser.parse("return x = hello"))  # test cmd
    print(parser.parse("set x = goodbye"))
    print(parser.parse("append to x with world"))


if __name__ == '__main__':
    main()


