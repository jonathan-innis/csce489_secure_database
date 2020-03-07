import sys
from lark import Lark, tree, Transformer
from lark.exceptions import UnexpectedCharacters
from db.permissions import Right
from db.database import Database, PrincipalKeyError, SecurityViolation

# TODO: prog needs to always be starting command
# TODO: fix line 37 38 -> p ???

GRAMMAR = """
start:      auth EOL cmd EOL "***"

auth:       "as principal" IDENT "password" S "do"                      -> auth_call 

cmd:        "exit"                                                      -> exit_call                    
            | "return " expr                                            -> end_return_call
            | prim_cmd EOL cmd
            
expr:       value                                                       -> val_call
            | "[]"                                                      -> list_call                                                                        
            | dict                                                      -> val_call

dict:       "{" fieldvals "}"                                           -> val_call

fieldvals:  IDENT "=" value                                             -> field_base_call
            | IDENT "=" value "," fieldvals                             -> field_recur_call
            
value:      IDENT                                                       -> return_val_call                                                                                        
            | IDENT "." IDENT                                           -> return_dot_call
            | S                                                         -> string_call

prim_cmd:   "create principal" IDENT S                                  -> create_principal_call
            | "change password" IDENT S                                 -> change_password_call
            | "set" IDENT "=" expr                                      -> set_call
            | "append to" IDENT "with" expr                             -> append_call
            | "local" IDENT "=" expr
            | "foreach" IDENT "in" IDENT "replacewith" foreach_str      -> foreach_call
            | "set delegation " TGT IDENT right "->" IDENT              -> set_delegation_call
            | "delete delegation " TGT IDENT right "->" IDENT           -> delete_delegation_call
            | "default delegator =" IDENT                               -> default_delegator_call
            
right:      READ                                                        -> read_right_call                                          
            | WRITE                                                     -> write_right_call
            | APPEND                                                    -> append_right_call
            | DELEGATE                                                  -> delegate_right_call

foreach_str:    val_str                                                 -> val_call
                | "[]"                                                  -> val_call
                | dict_str                                              -> val_call

dict_str: "{" field_str "}"                                             -> dict_str_call

field_str:  IDENT "=" val_str                                           -> field_str_base_call
            | IDENT "=" val_str "," field_str                           -> field_str_recur_call

val_str:    IDENT                                                       -> val_call
            | IDENT "." IDENT                                           -> dot_str_call
            | S                                                         -> string_call

READ: "read"
WRITE: "write"
APPEND: "append"
DELEGATE: "delegate"

EOL : " "* ( NEWLINE | /\f/)
COMMENT: "//" /(.)+/

TGT: (ALL | IDENT)
ALL: "all"
IDENT: /(?!all\s|append\s|as\s|change\s|create\s|default\s|delegate\s|delegation\s|delegator\s|delete\s|do\s|exit\s|foreach\s|in\s|local\s|password\s|principal\s|read\s|replacewith\s|return\s|set\s|to\s|write\s)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[A-Za-z0-9_,;\.?!-]*\w*"/

%import common.WORD
%import common.WS
%import common.NEWLINE
%ignore WS
%ignore COMMENT
"""

# Have to make a separate grammar for "for_each" processing

FOREACH_GRAMMAR = """

start:      expr                                                        -> val_call

expr:       value                                                       -> val_call
            | "[]"                                                      -> list_call                                                                        
            | dict                                                      -> val_call

dict:       "{" fieldvals "}"                                           -> val_call

fieldvals:  IDENT "=" value
            | IDENT "=" value "," fieldvals
            
value:      IDENT                                                       -> return_val_call                                                                                        
            | IDENT "." IDENT                                           -> return_dot_call
            | S                                                         -> string_call

TGT: (ALL | IDENT)
ALL: "all"
IDENT: /(?!all\s|append\s|as\s|change\s|create\s|default\s|delegate\s|delegation\s|delegator\s|delete\s|do\s|exit\s|foreach\s|in\s|local\s|password\s|principal\s|read\s|replacewith\s|return\s|set\s|to\s|write\s)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[A-Za-z0-9_,;\.?!-]*\w*"/

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
        try:
            p = str(args[0])
            pwd = str(args[1]).strip('"')
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
            self.d.create_principal(str(args[0]), str(args[1]).strip('"'))
            self.ret.append({"status": "CREATE_PRINCIPAL"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def change_password_call(self, args):
        try:
            self.d.change_password(str(args[0]), str(args[1]).strip('"'))
            self.ret.append({"status": "CHANGE_PASSWORD"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def set_call(self, args):
        try:
            self.d.set_record(str(args[0]), args[1])
            self.ret.append({"status": "SET"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def append_call(self, args):
        self.d.append_record(args[0], args[1])
    
    def foreach_call(self, args):
        try:
            parser = Lark(FOREACH_GRAMMAR, parser='lalr')
            tree = parser.parse(args[2])

            old_list = self.d.return_record(str(args[1]))

            if not isinstance(old_list, list):
                raise Exception("failed")

            new_list = []
            
            for elem in old_list:
                self.d.set_record(args[0], elem)
                new_val = T(self.d).transform(tree)

                if isinstance(new_val, list):
                    raise Exception("failed")
                new_list.append(new_val)
            
            self.d.delete_record(args[0]) # delete the record used for temps
            self.d.set_record(str(args[1]), new_list)
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def field_base_call(self, args):
        return {str(args[0]): args[1]}

    def field_recur_call(self, args):
        record = args[2]
        record[str(args[0])] = args[1]
        return record

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

    def read_right_call(self, args):
        return Right.READ

    def write_right_call(self, args):
        return Right.WRITE
    
    def append_right_call(self, args):
        return Right.APPEND

    def delegate_right_call(self, args):
        return Right.DELEGATE

    def all_call(self, args):
        return "all"

    # String methods used for the for each processing

    def dict_str_call(self, args):
        return "{" + args[0] + "}"

    def field_str_base_call(self, args):
        return args[0] + "=" + args[1]

    def field_str_recur_call(self, args):
        return args[0] + "=" + args[1] + "," + args[2]

    def dot_str_call(self, args):
        return args[0] + "." + args[1]

def parse(database, text):
    parser = Lark(GRAMMAR, parser='lalr')

    # try:
    tree = parser.parse(text)
    t = T(database)
    t.transform(tree)
    return t.ret

    # Catching Exceptions that are by the database and the parser
    # except UnexpectedCharacters as e:
    #     print(e)
    #     return {"status": "FAILED"}
    # except Exception as e:
    #     print(e)
    #     if str(e.__context__) == "denied":
    #         return {"status": "DENIED"}
    #     else:
    #         return {"status": "FAILED"}

def main():
    d = Database("test")
    text1 = 'as principal admin password "test" do \n set x = [] \n append to x with {name="jonathan", elem="body"} \n append to x with {name="reuben"} \n foreach y in x replacewith y.name \n return x \n ***'
    text2 = 'as principal bobby password "newpassword" do \n return x \n ***'
    text3 = 'as principal admin password "test" do \n foreach y in x replacewith {x=str, y="str"} \n exit \n ***'
    # print(parser.parse("exit").pretty())  # test cmd
    # print(parser.parse("create principal prince").pretty())  # test prim cmd
    # print(parser.parse("return x = hello").pretty())  # test cmd
    # print(parser.parse("set x = goodbye").pretty())
    # print(parser.parse("append to x with world").pretty())
    print(parse(d, text1))
    # print(parse(d, text2))
    # print(parse(d, text3))

if __name__ == '__main__':
    main()    
