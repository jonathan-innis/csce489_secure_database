import sys
from lark import Lark, tree, Transformer
from lark.exceptions import UnexpectedCharacters
from db.permissions import Right
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
            | "local " x "=" expr
            | "foreach " y " in " x " replacewith " expr
            | "set delegation " tgt q right "->" p          -> set_delegation_call
            | "delete delegation " tgt q right "->" p       -> delete_delegation_call
            | "default delegator =" p                       -> default_delegator_call
            
tgt:        "all"
            | x                                             -> val_call
            
right:      "read"                                          -> read_call                                          
            | "write"                                       -> write_call
            | "append"                                      -> append_call
            | "delegate"                                    -> delegate_call

EOL : " "* ( NEWLINE | /\f/)
COMMENT: "//" /(.)+/


p: /[A-Za-z][A-Za-z0-9_]*/                                  -> val_call
q: /[A-Za-z][A-Za-z0-9_]*/                                  -> val_call
s: /"[A-Za-z0-9_,;\.?!-]*"/                                 -> string_call
x: /[A-Za-z][A-Za-z0-9_]*/                                  -> val_call
y: /[A-Za-z][A-Za-z0-9_]*/                                  -> val_call

%import common.WORD
%import common.WS
%import common.NEWLINE
%ignore WS
%ignore COMMENT
"""


class T(Transformer):

    def __init__(self, d):
        self.d = d
        self.ret = []

    def auth_call(self, args):
        try:
            p = str(args[0])
            pwd = str(args[1])
            self.d.set_principal(p, pwd)
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def string_call(self, args):
        return str(args[0].strip('"'))

    def val_call(self, args):
        return args[0]

    def return_val_call(self, args):
        try:
            val = str(args[0])
            return self.d.return_record(val)
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def return_dot_call(self, args):
        try:
            val = str(args[0]) + "." + str(args[1])
            return self.d.return_record(val)
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def end_return_call(self, args):
        self.ret.append({"status": "RETURNING", "output": args[0]})

    def list_call(self, args):
        return []

    def create_principal_call(self, args):
        try:
            self.d.create_principal(str(args[0]), str(args[1]))
            self.ret.append({"status": "CREATE_PRINCIPAL"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def change_password_call(self, args):
        try:
            self.d.change_password(str(args[0]), str(args[1]))
            self.ret.append({"status": "CHANGE_PASSWORD"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def set_call(self, args):
        try:
            self.d.set_record(args[0], args[1])
            self.ret.append({"status": "SET"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def set_delegation_call(self, args):
        try:
            self.d.set_delegation(args[0], args[1], args[3], args[2])
            self.ret.append({"status": "SET_DELEGATION"})

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def delete_delegation_call(self, args):
        try:
            self.d.delete_delegation(args[0], args[1], args[3], args[2])
            self.ret.append({"status": "DELETE_DELEGATION"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def default_delegator_call(self, args):
        try:
            self.d.set_default_delegator(args[0])
            self.ret.append({"status": "DEFAULT_DELEGATOR"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def read_call(self, args):
        return Right.READ

    def write_call(self, args):
        return Right.WRITE
    
    def append_call(self, args):
        return Right.APPEND

    def delegate_call(self, args):
        return Right.DELEGATE

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
        print(e)
        return {"status": "FAILED"}
    except Exception as e:
        if str(e.__context__) == "denied":
            return {"status": "DENIED"}
        else:
            return {"status": "FAILED"}

def main():
    d = Database("test")
    text1 = 'as principal admin password "test" do \n set x = [] \n create principal bobby "password" \n change password bobby "newpassword" \n set delegation x admin read->bobby \n return x \n ***'
    text2 = 'as principal bobby password "newpassword" do \n return x \n ***'
    text3 = 'as principal admin password "test" do \n create principal read "password" \n exit \n ***'
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())
    print(parse(d, text1))
    print(parse(d, text2))
    print(parse(d, text3))


if __name__ == '__main__':
    main()    
