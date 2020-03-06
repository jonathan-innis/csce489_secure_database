import sys
from lark import Lark, tree, Transformer
from lark.exceptions import UnexpectedCharacters
from db.database import Database, PrincipalKeyError, SecurityViolation
from db.principal import Principal


# TODO: prog needs to always be starting command
# TODO: fix line 37 38 -> p ???

GRAMMAR = """
start:      auth EOL cmd EOL "***"

auth:       "as principal " p " password " s " do"          -> auth_call 

cmd:        "exit"                                          -> exit_call                    
            | "return " expr                                -> end_return_call
            | prim_cmd EOL cmd
            
expr:       value                                           -> val_call
            | "[]"                                          -> list_call                                                                        
            | fieldvals
            
fieldvals:  x "=" value
            | x "=" value "," fieldvals
            
value:      x                                               -> return_val_call                                                                                        
            | x "." y                                       -> return_dot_call
            | s                                             -> string_call                                      

prim_cmd:   "create principal " p s                         -> create_principal_call
            | "change password " p s                        -> change_password_call
            | "set " x "=" expr                             -> set_call
            | "append to " x " with " expr
            | "local " x " = " expr
            | "foreach " y " in " x " replacewith " expr
            | "set delegation " tgt q right -> p
            | "delete delegation " tgt q right -> p
            | "default delegator = " p                      -> default_delegator_call
            
tgt:        "all"
            | x
            
right:      "read"
            | "write"
            | "append"
            | "delegate"

EOL : " "* ( NEWLINE | /\f/)


p: /[A-Za-z][A-Za-z0-9_]*/                                  -> string_call
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
        self.d = d
        self.ret = []

    def auth_call(self, args):
        p = str(args[0])
        pwd = str(args[1])
        self.d.set_principal(p, pwd)

    def string_call(self, args):
        return str(args[0].strip('"'))

    def val_call(self, args):
        return args[0]

    def return_val_call(self, args):
        val = str(args[0])
        return self.d.return_record(val)

    def return_dot_call(self, args):
        val = str(args[0]) + "." + str(args[1])
        return self.d.return_record(val)

    def end_return_call(self, args):
        self.ret.append({"status": "RETURNING", "output": args[0]})

    def list_call(self, args):
        return []

    def create_principal_call(self, args):
        self.d.create_principal(str(args[0]), str(args[1]))
        self.ret.append({"status": "CREATE_PRINCIPAL"})

    def change_password_call(self, args):
        self.d.change_password(str(args[0]), str(args[1]))
        self.ret.append({"status": "CHANGE_PASSWORD"})

    def set_call(self, args):
        self.d.set_record(args[0], args[1])
        self.ret.append({"status": "SET"})

    def default_delegator_call(self, args):
        try:
            self.d.set_default_delegator(args[0])
            self.ret.append({"status": "DEFAULT_DELEGATOR"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def exit_call(self, args):
        print("EXITING")


def parse(database, text):
    parser = Lark(GRAMMAR)

    try:
        tree = parser.parse(text)
        t = T(database)
        t.transform(tree)
        return t.ret

    # Catching Exceptions that are by the database and the parser
    except UnexpectedCharacters as e:
        return {"status": "FAILED"}
    except Exception as e:
        if str(e.__context__) == "failed":
            return {"status": "FAILED"}
        elif str(e.__context__) == "denied":
            return {"status": "DENIED"}

def main():
    d = Database("test")
    text1 = 'as principal admin password "test" do \n set x = [] \n create principal bobby "password" \n change password bobby "newpassword" \n return x \n ***'
    text2 = 'as principal bobby password "newpassword" do \n exit \n ***'
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())
    print(parse(d, text1))


if __name__ == '__main__':
    main()    
