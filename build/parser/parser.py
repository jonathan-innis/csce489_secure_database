import sys
from lark import Lark, tree, Transformer
from lark.exceptions import UnexpectedCharacters
from db.permissions import Right
from db.permissions import Right
from db.database import Database, PrincipalKeyError, SecurityViolation


GRAMMAR = """
start:      _WS? auth _WS? EOL _WS? cmd _WS? EOL _WS? "***" _WS?

auth:       "as" _WS "principal" _WS IDENT _WS "password" _WS S _WS "do"                    -> auth_call 

cmd:        "exit"                                                                          -> exit_call                    
            | "return" _WS expr                                                             -> end_return_call
            | prim_cmd _WS? EOL _WS? cmd _WS?
            
expr:       value                                                                           -> val_call
            | "[]"                                                                          -> list_call                                                                        
            | dict                                                                          -> val_call

dict:       "{" _WS? fieldvals _WS? "}"                                                     -> val_call

fieldvals:  base_fieldval _WS?                                                              -> val_call
            | base_fieldval _WS? "," _WS? fieldvals                                         -> field_recur_call

base_fieldval: IDENT _WS? "=" _WS? value                                                    -> field_base_call

value:      IDENT _WS?                                                                      -> return_val_call                                                                                        
            | IDENT _WS? "." _WS? IDENT                                                     -> return_dot_call
            | S                                                                             -> string_call

prim_cmd:   "create" _WS "principal" _WS IDENT _WS S                                        -> create_principal_call
            | "change" _WS "password" _WS IDENT _WS S                                       -> change_password_call
            | _SET _WS IDENT _WS? "=" _WS? expr                                             -> set_call
            | "append" _WS "to" _WS IDENT _WS "with" _WS expr                               -> append_call
            | "local" _WS IDENT _WS? "=" _WS? expr                                          -> local_call
            | "foreach" _WS IDENT _WS "in" _WS IDENT _WS "replacewith" _WS foreach_str      -> foreach_call
            | _SET_DELEGATION _WS TGT _WS IDENT _WS right _WS? "->" _WS? IDENT              -> set_delegation_call
            | "delete" _WS "delegation" _WS TGT _WS IDENT _WS right _WS? "->" _WS? IDENT    -> delete_delegation_call
            | "default" _WS "delegator" _WS "=" _WS? IDENT                                  -> default_delegator_call
            
right:      READ                                                                            -> read_right_call                                          
            | WRITE                                                                         -> write_right_call
            | APPEND                                                                        -> append_right_call
            | DELEGATE                                                                      -> delegate_right_call

foreach_str:    val_str                                                                     -> val_call
                | "[]"                                                                      -> val_call
                | dict_str                                                                  -> val_call

dict_str: "{" _WS? field_str _WS? "}"                                                       -> dict_str_call

field_str:  IDENT _WS? "=" _WS? val_str                                                     -> field_str_base_call
            | IDENT _WS? "=" _WS? val_str _WS? "," _WS? field_str                           -> field_str_recur_call

val_str:    IDENT                                                                           -> val_call
            | IDENT _WS? "." _WS? IDENT                                                     -> dot_str_call
            | S                                                                             -> val_call

READ: "read"
WRITE: "write"
APPEND: "append"
DELEGATE: "delegate"

_SET_DELEGATION: "set" _WS "delegation"
_SET: "set"

EOL : " "* ( NEWLINE | /\f/)
COMMENT: "//" /(.)+/

TGT: (ALL | IDENT)
ALL: "all"
IDENT: /(?!all\s|append\s|as\s|change\s|create\s|default\s|delegate\s|delegation\s|delegator\s|delete\s|do\s|exit\s|foreach\s|in\s|local\s|password\s|principal\s|read\s|replacewith\s|return\s|set\s|to\s|write\s)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[ A-Za-z0-9_,;\.?!-]*"/

%import common.WORD
%import common.WS_INLINE -> _WS
%import common.NEWLINE
%ignore COMMENT
"""

# Have to make a separate grammar for "for_each" processing

FOREACH_GRAMMAR = """

start:      expr                                                        -> val_call

expr:       value                                                       -> val_call
            | "[]"                                                      -> list_call                                                                        
            | dict                                                      -> val_call

dict:       "{" _WS? fieldvals _WS? "}"                                 -> val_call

fieldvals:  base_fieldval _WS?                                          -> val_call
            | base_fieldval _WS? "," _WS? fieldvals                     -> field_recur_call

base_fieldval: IDENT _WS? "=" _WS? value                                -> field_base_call
            
value:      IDENT _WS?                                                  -> return_val_call                                                                                        
            | IDENT _WS? "." _WS? IDENT                                 -> return_dot_call
            | S                                                         -> string_call

TGT: (ALL | IDENT)
ALL: "all"
IDENT: /(?!all\s|append\s|as\s|change\s|create\s|default\s|delegate\s|delegation\s|delegator\s|delete\s|do\s|exit\s|foreach\s|in\s|local\s|password\s|principal\s|read\s|replacewith\s|return\s|set\s|to\s|write\s)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[ A-Za-z0-9_,;\.?!-]*"/

%import common.WORD
%import common.WS_INLINE -> _WS
%import common.NEWLINE

"""


class T(Transformer):

    def __init__(self, d):
        self.d = d
        self.ret = []

    def auth_call(self, args):
        try:
            p = str(args[0])
            pwd = str(args[1]).strip('"')
            print(p, pwd)
            self.d.set_principal(p, pwd)
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def exit_call(self, args):
        try:
            self.d.exit()
            self.ret.append({"status": "EXITING"})
    
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
            print(args)
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
        try:
            self.d.append_record(args[0], args[1])
            self.ret.append({"status": "APPEND"})

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def local_call(self, args):
        try:
            self.d.set_local_record(str(args[0]), args[1])
            self.ret.append({"status": "LOCAL"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")
    
    def foreach_call(self, args):
        try:
            print(args[2])
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
            self.ret.append({"status": "FOREACH"})
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def field_base_call(self, args):
        if not isinstance(args[1], str):
            raise Exception("failed")
        return {str(args[0]): args[1]}

    def field_recur_call(self, args):
        record = args[1]
        for k, v in args[0].items():
            if k in record:
                raise Exception("failed")
            record[k] = v
        return record

    def set_delegation_call(self, args):
        try:
            self.d.set_delegation(args[0], str(args[1]), str(args[3]), args[2])
            self.ret.append({"status": "SET_DELEGATION"})

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def delete_delegation_call(self, args):
        try:
            self.d.delete_delegation(args[0], str(args[1]), str(args[3]), args[2])
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
    try:
        parser = Lark(GRAMMAR, parser='lalr')
        tree = parser.parse(text)
        t = T(database)
        t.transform(tree)
        return t.ret

    # Catching Exceptions that are by the database and the parser
    except UnexpectedCharacters as e:
        print(e)
        return [{"status": "FAILED"}]
    except Exception as e:
        print(e)
        if str(e.__context__) == "denied":
            return [{"status": "DENIED"}]
        else:
            return [{"status": "FAILED"}]  