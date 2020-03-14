import sys
from lark import Lark, tree, Transformer
from lark.exceptions import UnexpectedCharacters
from db.permissions import Right
from db.permissions import Right
from db.database import Database, PrincipalKeyError, SecurityViolation

#TODO: Remove all the print statements from debugging

GRAMMAR = """
start:      _WS? auth _WS? EOL _WS? cmd _WS? EOL _WS? "***" _WS?

auth:       "as" _WS "principal" _WS IDENT _WS "password" _WS S _WS "do"                    -> auth_call 

cmd:        "exit"                                                                          -> exit_call                    
            | "return" _WS expr                                                             -> end_return_call
            | prim_cmd _WS? EOL _WS? cmd _WS?
            
expr:       _LET _WS recursive                                                              -> val_call
            | "[]"                                                                          -> list_call                                                                        
            | dict                                                                          -> val_call
            | func                                                                          -> val_call
            | value                                                                         -> val_call

dict:       "{" _WS? fieldvals _WS? "}"                                                     -> val_call

func:       "split" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                        -> split_call
            | "concat" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                     -> concat_call
            | "tolower" _WS? "(" _WS? value _WS? ")"                                        -> tolower_call
            | "equal" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                      -> equal_call
            | "notequal" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                   -> notequal_call

recursive:   recursive_start _WS recursive_end                                              -> recursive_call

recursive_start: IDENT _WS? "=" _WS? expr                                                   -> recursive_start_call

recursive_end: "in" _WS expr                                                                -> val_call

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
            | "foreach" _WS IDENT _WS "in" _WS IDENT _WS "replacewith" _WS expr_str         -> foreach_call
            | "filtereach" _WS IDENT _WS "in" _WS IDENT _WS "with" _WS expr_str             -> filtereach_call
            | _SET_DELEGATION _WS TGT _WS IDENT _WS right _WS? "->" _WS? IDENT              -> set_delegation_call
            | "delete" _WS "delegation" _WS TGT _WS IDENT _WS right _WS? "->" _WS? IDENT    -> delete_delegation_call
            | "default" _WS "delegator" _WS "=" _WS? IDENT                                  -> default_delegator_call
            
right:      READ                                                                            -> read_right_call                                          
            | WRITE                                                                         -> write_right_call
            | APPEND                                                                        -> append_right_call
            | DELEGATE                                                                      -> delegate_right_call

expr_str:   _LET _WS IDENT _WS? "=" _WS? expr_str _WS "in" _WS expr_str                     -> recursive_str_call
            | "[]"                                                                          -> val_call
            | "{" _WS? field_str _WS? "}"                                                   -> dict_str_call
            | func_str                                                                      -> val_call
            | val_str                                                                       -> val_call

field_str:  IDENT _WS? "=" _WS? val_str                                                     -> field_str_base_call
            | IDENT _WS? "=" _WS? val_str _WS? "," _WS? field_str                           -> field_str_recur_call

val_str:    IDENT                                                                           -> val_call
            | IDENT _WS? "." _WS? IDENT                                                     -> dot_str_call
            | S                                                                             -> val_call

func_str:   "split" _WS? "(" _WS? val_str _WS? "," _WS? val_str _WS? ")"                    -> split_str_call
            | "concat" _WS? "(" _WS? val_str _WS? "," _WS? val_str _WS? ")"                 -> concat_str_call
            | "tolower" _WS? "(" _WS? val_str _WS? ")"                                      -> tolower_str_call
            | "equal" _WS? "(" _WS? val_str _WS? "," _WS? val_str _WS? ")"                  -> equal_str_call
            | "notequal" _WS? "(" _WS? val_str _WS? "," _WS? val_str _WS? ")"               -> notequal_str_call


READ: "read"
WRITE: "write"
APPEND: "append"
DELEGATE: "delegate"

_SET_DELEGATION: "set" _WS "delegation"
_SET: "set"

EOL : " "* ( NEWLINE | /\f/)
COMMENT: (SAME_LINE_COMMENT | FULL_LINE_COMMENT)
SAME_LINE_COMMENT: _WS? "//" /[A-Za-z0-9_ ,;\.?!-]*/
FULL_LINE_COMMENT: EOL "//" /[A-Za-z0-9_ ,;\.?!-]*/

TGT: (ALL | IDENT)
_LET.2: "let"
ALL: "all"
IDENT: /(?!all|append|as|change|create|default|delegate|delegation|delegator|delete|do|exit|foreach|in|local|password|principal|read|replacewith|return|set|to|write|split|concat|tolower|notequal|equal|filtereach|with|let)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[ A-Za-z0-9_,;\.?!-]*"/

_WS: (" ")+

%import common.WORD
%import common.NEWLINE
%ignore COMMENT
"""

# Have to make a separate grammar for "for_each" processing

FOREACH_GRAMMAR = """

start:      expr                                                                            -> val_call

expr:       _LET _WS recursive                                                              -> val_call
            | "[]"                                                                          -> list_call                                                                        
            | dict                                                                          -> val_call
            | func                                                                          -> val_call
            | value                                                                         -> val_call

dict:       "{" _WS? fieldvals _WS? "}"                                                     -> val_call

func:       "split" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                        -> split_call
            | "concat" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                     -> concat_call
            | "tolower" _WS? "(" _WS? value _WS? ")"                                        -> tolower_call
            | "equal" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                      -> equal_call
            | "notequal" _WS? "(" _WS? value _WS? "," _WS? value _WS? ")"                   -> notequal_call

recursive:   recursive_start _WS recursive_end                                              -> recursive_call

recursive_start: IDENT _WS? "=" _WS? expr                                                   -> recursive_start_call

recursive_end: "in" _WS expr                                                                -> val_call

fieldvals:  base_fieldval _WS?                                                              -> val_call
            | base_fieldval _WS? "," _WS? fieldvals                                         -> field_recur_call

base_fieldval: IDENT _WS? "=" _WS? value                                                    -> field_base_call
            
value:      IDENT _WS?                                                                      -> return_val_call                                                                                        
            | IDENT _WS? "." _WS? IDENT                                                     -> return_dot_call
            | S                                                                             -> string_call

TGT: (ALL | IDENT)
ALL: "all"
_LET.2: "let"
IDENT: /(?!all|append|as|change|create|default|delegate|delegation|delegator|delete|do|exit|foreach|in|local|password|principal|read|replacewith|return|set|to|write|split|concat|tolower|notequal|equal|filtereach|with|let)([A-Za-z][A-Za-z0-9_]*)/                                  
S: /"[ A-Za-z0-9_,;\.?!-]*"/

_WS: (" ")+

%import common.WORD
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
            print(args)
            val = str(args[0])
            return self.d.return_record(val)
        
        except SecurityViolation as e:
            print(e)
            raise Exception("denied")
        except Exception as e:
            print(e)
            raise Exception("failed")

    def return_dot_call(self, args):
        try:
            val = str(args[0]) + "." + str(args[1])
            print(val)
            return self.d.return_record(val)
        
        except SecurityViolation as e:
            print(e)
            raise Exception("denied")
        except Exception as e:
            print(e)
            raise Exception("failed")

    def end_return_call(self, args):
        self.ret.append({"status": "RETURNING", "output": args[0]})

    def list_call(self, args):
        return []

    def split_call(self, args):
        try:
            if not isinstance(args[0], str) or not isinstance(args[1], str):
                raise Exception("failed")
            res = {
                    "fst": args[0][:len(args[1])],
                    "snd": args[0][len(args[1]):]
                }
            return res

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")
    
    def concat_call(self, args):
        try:
            if not isinstance(args[0], str) or not isinstance(args[1], str):
                raise Exception("failed")
            res = args[0] + args[1]
            return res[:65535]
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def tolower_call(self, args):
        try:
            if not isinstance(args[0], str):
                raise Exception("failed")
            return args[0].lower()

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def equal_call(self, args):
        try:
            if isinstance(args[0], list) or isinstance(args[1], list):
                raise Exception("failed")
            elif isinstance(args[0], str) and isinstance(args[1], str):
                if args[0] == args[1]:
                    return ""
                return "0"
            elif isinstance(args[0], dict) and isinstance(args[1], dict):
                for k in args[0]:
                    if k not in args[1]:
                        return "0"
                    if args[0][k] != args[1][k]:
                        return "0"
                return ""
            else:
                raise Exception("failed")

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def notequal_call(self, args):
        try:
            if self.equal_call(args) == "":
                return "0"
            return ""
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def recursive_call(self, args):
        try:
            self.d.delete_record(args[0])
            return args[1]

        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

    def recursive_start_call(self, args):
        try:
            self.d.set_local_record(str(args[0]), args[1])
            return str(args[0])
        
        except SecurityViolation as e:
            raise Exception("denied")
        except Exception as e:
            raise Exception("failed")

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
            print(e)
            raise Exception("denied")
        except Exception as e:
            print(e)
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
            print(args)
            parser = Lark(FOREACH_GRAMMAR, parser='lalr')
            tree = parser.parse(args[2])

            old_list = self.d.return_record(str(args[1]))

            if not isinstance(old_list, list):
                raise Exception("failed")

            new_list = []
            
            for elem in old_list:
                self.d.set_local_record(args[0], elem)
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

    def filtereach_call(self, args):
        try:
            parser = Lark(FOREACH_GRAMMAR, parser='lalr')
            tree = parser.parse(args[2])

            old_list = self.d.return_record(str(args[1]))

            if not isinstance(old_list, list):
                raise Exception("failed")

            new_list = []

            for elem in old_list:
                self.d.set_local_record(args[0], elem)
                result = T(self.d).transform(tree)
                if result == "":
                    new_list.append(elem)
                self.d.delete_record(args[0]) # delete the record used for temps

            self.d.set_record(str(args[1]), new_list)
            self.ret.append({"status": "FILTEREACH"})
        
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

    def args_recur_call(self, args):
        return [args[0]] + args[1]
    
    def args_base_call(self, args):
        if not isinstance(args[0], str):
            raise Exception("failed")
        return args[0]

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

    def split_str_call(self, args):
        return "split(" + args[0] + "," + args[1] + ")"

    def concat_str_call(self, args):
        return "concat(" + args[0] + "," + args[1] + ")"

    def tolower_str_call(self, args):
        return "tolower(" + args[0] + ")"

    def equal_str_call(self, args):
        return "equal(" + args[0] + "," + args[1] + ")"

    def notequal_str_call(self, args):
        return "notequal(" + args[0] + "," + args[1] + ")"

    def recursive_str_call(self, args):
        return "let " + args[0] + "=" + args[1] + " in " + args[2]

class Parser:
    def __init__(self):
        self.parser = Lark(GRAMMAR, parser='lalr')

    def parse(self, database, text):
        try:
            tree = self.parser.parse(text)
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