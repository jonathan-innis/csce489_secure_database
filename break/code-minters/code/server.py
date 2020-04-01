#!/usr/bin/python
import socket
import sys
import re
import json
import ast
import hashlib
import copy
import signal
import ctypes
import pickle

KEY_WORDS = {"all":1, "append":1, "as":1, "change":1, "create":1, "default":1,
    "delegate":1, "delegation":1, "delegator":1, "delete":1, "do":1, "exit":1,
    "foreach":1, "in":1, "local":1, "password":1, "principal":1, "read":1,
    "replacewith":1, "return":1, "set":1, "to":1, "write":1, "***":1,
    "split":1, "concat":1, "tolower":1, "notequal":1, "filtereach":1, "with":1,
    "let":1,
}

S = "\"[A-Za-z0-9_ ,;\.?!-]*\""
PARSE_S = "\"([A-Za-z0-9_ ,;\.?!-]*)\""
X = "[A-Za-z][A-Za-z0-9_]*"
TGT = "all|%s" % (X)
RIGHT = "read|write|append|delegate"

VALUE= "%s|%s[ ]*.[ ]*%s|%s" % (S,X,X,X)

FIELDVALS = "%s[ ]*=[ ]*[A-Za-z0-9_ ,;\.?!-= ]+" % (X)

EXPR = "%s|[{][ ]*%s[ ]*[}]|\[\]" % (VALUE,FIELDVALS)

PROG = "^(as[ ]+principal)[ ]+%s[ ]+password[ ]+%s[ ]+do[ ]*$" % (X,S)
PARSE_PROG = "^[ ]*as[ ]+principal[ ]+(%s)[ ]+password[ ]+%s[ ]+do[ ]*$" % (X,PARSE_S)

CREATE_PRIN = "^create[ ]+principal[ ]+%s[ ]+%s[ ]*$" % (X,S)
PARSE_CREATE = "^[ ]*create[ ]+principal[ ]+(%s)[ ]+%s[ ]*$" % (X,PARSE_S)

CHANGE_PRIN = "^change[ ]+password[ ]+%s[ ]+%s[ ]*$" % (X,S)
PARSE_CHANGE = "^[ ]*change[ ]+password[ ]+(%s)[ ]+%s[ ]*$" % (X,PARSE_S)

SET = "^(set)[ ]+%s[ ]+=[ ]+%s[ ]*$" % (X,EXPR)
PARSE_SET = "^[ ]*set[ ]+(%s)[ ]+=[ ]+(%s)[ ]*$" % (X,EXPR)

APPEND = "^append[ ]+to[ ]+%s[ ]+with[ ]+%s[ ]*$" % (X,EXPR)
PARSE_APPEND = "^[ ]*append[ ]+to[ ]+(%s)[ ]+with[ ]+(%s)[ ]*$" % (X,EXPR)

LOCAL = "^local[ ]+%s[ ]+=[ ]+%s[ ]*$" % (X,EXPR)
PARSE_LOCAL = "^[ ]*local[ ]+(%s)[ ]+=[ ]+(%s)[ ]*$" % (X,EXPR)

FOREACH = "^foreach[ ]+%s[ ]+in[ ]+%s[ ]+replacewith[ ]+%s[ ]*$" % (X,X,EXPR)
PARSE_FOREACH = "^[ ]*foreach[ ]+(%s)[ ]+in[ ]+(%s)[ ]+replacewith[ ]+(%s)[ ]*$" % (X,X,EXPR)

SET_DEL = "^(set[ ]+delegation)[ ]+%s[ ]+%s[ ]+%s[ ]+->[ ]+%s[ ]*$" % (TGT,X,RIGHT,X)
PARSE_SET_DEL = "^[ ]*set[ ]+delegation[ ]+(%s)[ ]+(%s)[ ]+(%s)[ ]+->[ ]+(%s)[ ]*$" % (TGT,X,RIGHT,X)

DEL_DEL = "^delete[ ]+delegation[ ]+%s[ ]+%s[ ]+%s[ ]+->[ ]+%s[ ]*$" % (TGT,X,RIGHT,X)
PARSE_DEL_DEL = "^[ ]*delete[ ]+delegation[ ]+(%s)[ ]+(%s)[ ]+(%s)[ ]+->[ ]+(%s)[ ]*$" % (TGT,X,RIGHT,X)

DEF_DEL = "^default[ ]+delegator[ ]+=[ ]+%s[ ]*$" % (X)
PARSE_DEF_DEL = "^[ ]*default[ ]+delegator[ ]+=[ ]+(%s)[ ]*$" % (X)

TERMIN = "^[ ]*\*\*\*[ ]*$"

EXIT = "^exit[ ]*$"

RETURN = "^(return)%s[ ]*$" % (EXPR)
PARSE_RETURN = "^[ ]*return(%s)[ ]*$" % (EXPR)

def sigterm_handler(_signo, _stack_frame):
    exit(0)

class status:

    def __init__(self, type, output = ""):
        self.type = type
        self.output = output
    def JSON(self):
        x = {}
        if self.type == "RETURNING":
            x = {"status": "RETURNING", "output": self.output}
        else:
            x = {"status": self.type}
        y = json.dumps(x)
        return y

class principal:
    def __init__(self, u, p):
        self.u = u
        self.p = p #simple hash
        self.delegations = [] # change {} to []

    def has_delegation(self, obj):
        '''
            For the `object` which is the key in `lexer.ol`
            Check if `self` exists in `dm_row[1]`
            Check if READ is a <right> in `dm_row[3]`
        '''
        if self.u == "admin":
            return True
        for d in self.delegations:
            if d.obj == obj:
                if d.dest.u == self:
                    if d.type == "delegate":
                        return d.origin.has_delegation(obj)

        return False
    def has_read(self, obj):
        '''
            For the `object` which is the key in `lexer.ol`
            Check if `self` exists in `dm_row[1]`
            Check if READ is a <right> in `dm_row[3]`
        '''
        if self.u == "admin":
            return True
        for d in self.delegations:
            if d.obj == obj:
                if d.dest == self:
                    if d.type == "read":
                        return d.origin.has_read(obj)

        return False
    def has_write(self, obj):
        '''
            For the `object` which is the key in `lexer.ol`
            Check if `self` exists in `dm_row[1]`
            Check if WRITE is a <right> in `dm_row[3]`
        '''
        if self.u == "admin":
            return True
        for d in self.delegations:
            if d.obj == obj:
                if d.dest == self:
                    if d.type == "write":
                        return d.origin.has_write(obj)

        return False
    def has_append(self, obj):
        '''
            For the `object` which is the key in `lexer.ol`
            Check if `self` exists in `dm_row[1]`
            Check if APPEND is a <right> in `dm_row[3]`
        '''
        if self.u == "admin":
            return True
        for d in self.delegations:
            if d.obj == obj:
                if d.dest == self:
                    if d.type == "append":
                        return d.origin.has_append(obj)

        return False
    def get_delegateable(self):
        '''
            For a given `delegator` (self=principal)
            Foreach `self` that exists in `dm_row[1]`
            Add `dm_row[0]` (ol global var) to `dm_list`
            return `dm_list`
        '''
        dm_list = []
        for d in self.delegations:
            if d.type == "delegate" and self.has_delegation(d.obj):
                dm_list.append(d.obj)
        return dm_list

class principal_list:
    def __init__(self, password):
        self.list = {}
        self.list["admin"] = principal("admin", ("admin", password)[password != ""])
    def add_principal(self, user, password):
        if user != "admin" and password != "":
            self.list[user] = principal(user, password)
    def remove_principal(self, user):
        if user != "admin":
            self.list.pop(user)
class program:
    def __init__(self):
        self.principal = None
        self.local = {}
        self.queue = {}
class delegation:
    def __init__(self, obj, origin, dest, t):
        self.obj = obj
        self.origin = origin
        self.dest = dest
        self.type = t
class delegation_map:
    def __init__(self):
        self.delegations = []
        self.default = None
    def is_exists(self, obj, origin, dest, t):
        for x in self.delegations:
            if x.obj == obj and x.origin == origin and x.dest == dest and x.type == t:
                return x
        return None
    def add_delegation(self, obj, origin, dest, t):
        x = self.is_exists(obj, origin, dest, t)
        #print("x = %s" %x)
        if x == None:
            # FIX type errors... objects being used instead of values?
            y = delegation(obj, origin, dest, t)
            #print("y obj = %s" % y.obj)
            #print("y origin = %s" % y.origin.u)
            #print("y dest = %s" % y.dest.u)
            #print("y type = %s" % y.type)
            self.delegations.append(y)
            #print("self = %s" % self.delegations)
            origin.delegations.append(y)
            #print("origin = %s" % origin.delegations)
            dest.delegations.append(y)
            #print("dest = %s" % dest.delegations)
            #print("\n***************************************\n")
    def remove_delegation(self, obj, origin, dest, t):
        x = self.is_exists(obj, origin, dest, t)
        if dest.u != "admin" and x != None:
            self.delegations.remove(x)
            origin.delegations.remove(x)
            dest.delegations.remove(x)
class lexer:
    def __init__(self, password):
        self.dm = delegation_map()
        self.pl = principal_list(password)
        self.ol = {}
    def expression(self, program, expression):
        #print("def expression called with %s" % expression)
        '''
            Concerns:
                What is PARSE_EXPR_FIELDVALS?
                Need to differ from x and x.y (two params or list?)
            From our Convo:
                expression is a list of matches from findall(PARSE...)
                expected to be only one result?
            Logic:
                expression[0] contains string of info from `<expr>`
                Make sure expression is not empty
                Check if `expression[0]` is a string
                Check ife`expression[0]` is a digit
                Check if `expression[0]` is a record.field
                Check if `expression[0]` is a variable
                Check if `expression[0]` is a fieldvalue
                Check if `expression[0]` is a []
                return (True|False, expression[0])

        '''
        if expression == "":
            return (2, "")
        elif expression[0] == "\"": # String
            #print("string found")
            if(len(expression) > 65535):
                return (1, expression)
            return (2, expression)
        elif expression.isdigit(): # Number
            return (2, expression)
        elif "{" in expression[0]:
            '''
                Convert the string dict {} into a dict object
                For each key/value pair in the dict
                check to see if it is an existing global or local variable
                check permission
            '''
            #print("{ elif")
            try:
                '''
                    Change the { name = "bob", age = 99 } to
                    { 'name': "bob", 'age':99 }
                    Then we can store as dict and make things eaiser
                '''
                tmp_expression = expression[1:-1]
                tmp_expression = tmp_expression.split(",")
                #print("exp remove {}  = %s " % tmp_expression)
                new_expression = {}
                for field in tmp_expression:
                    # field = key:value
                    #print("field is %s" % field)
                    key_value_pair = field.split("=") # 0 is key and 1 is value
                    #print("k:p plist is %s" %key_value_pair)
                    i = 0
                    for element in key_value_pair:
                        #print("element is %s" % element)
                        element = element.lstrip()
                        element = element.rstrip()
                        key_value_pair[i] = element
                        i += 1
                    #print("k:p nlist is %s" %key_value_pair)
                    if(key_value_pair[0] not in new_expression):
                        #print("new key value = %s" % key_value_pair[1])
                        r,exp = self.expression(program, key_value_pair[1])
                        if isinstance(exp, dict):
                            return (1, expression)
                        #print("r,exp = %s,%s" % (r,exp))
                        if r == 2:
                            new_expression[key_value_pair[0]] = exp
                        else:
                            return (r, expression)
                    else:
                        #print("Duplicate key error")
                        return (1, expression)
            except:
                #print("Unknown Error in expression { try block")
                return (1, expression)
            #print("exp finished = %s" % new_expression)
            return (2, new_expression)
        elif "[" in expression[0]:
            #print("empty list")
            return (2, [])
        elif "." in expression:
            '''
                Check Keywords
                Check if record exists
                Check has_read <right>
                Check if `x` in `x.y` exists in global or local
                Check if `y` exists in global or local record
            '''
            #print("elif . called")
            tmp_val = expression.split(".")
            if tmp_val[0] in KEY_WORDS or tmp_val[1] in KEY_WORDS:
                return (1, expression)
            # Check if record exists and has read <right>
            if tmp_val[0] not in self.ol and tmp_val[0] not in program.local:
                return (1, expression)
            if not program.principal.has_read(tmp_val[0]):
                return (0, expression)
            if tmp_val[0] in self.ol:
                # check if field exists in record
                if tmp_val[1] not in self.ol[tmp_val[0]]:
                    return (1, expression)
                return (2, self.ol[tmp_val[0]][tmp_val[1]])
            elif tmp_val[0] in program.local:
                # check if field exists in record
                if tmp_val[1] not in program.local[tmp_val[0]]:
                    return (1, expression)
                return (2, program.local[tmp_val[0]][tmp_val[1]])
        elif expression in self.ol:
            #print("self.ol variable found")
            if not program.principal.has_read(expression):
                #print("NO ACCESS ADSHJBASHJDABSHGDGHSA")
                return (0, expression)
            return (2, self.ol[expression])
        elif expression in program.local:
            #print("found in program.local expression()")
            if not program.principal.has_read(expression):
                return (0, expression)
            #print("passed has_read check = %s" % program.local[expression])
            return (2, program.local[expression])
        else:
            return (1, expression)

    def program_begin(self, program, user, password):
        if user in self.pl.list:
            if self.pl.list[user].p == password: # simple password hashing
                program.principal = self.pl.list[user]
                return 2
            return 0
        return 1
    def create_principal(self, program, user, password):
        #print("create princ  = %s,%s" % (user, password))
        if not user in self.pl.list:
            #print("User does not exist")
            if program.principal != None and program.principal.u == "admin":
                self.pl.list[user] = principal(user, password)
                #print("user added to pl list = %s" % self.pl.list[user])
                if self.dm.default != None:
                    #print("default %s" % self.dm.default)
                    #print("self.dm = %s" % self.dm)
                    for d in self.dm.delegations:
                        #print("u1,u2 = %s,%s" %(d.dest.u, self.dm.default.u))
                        if d.dest.u == self.dm.default.u:
                            self.dm.add_delegation(d.obj, self.pl.list["admin"], self.pl.list[user], d.type)
                return 2
            return 0
        #print("user = %s, pl.list = %s" % (user, self.pl.list))
        return 1
    def change_password(self, program, user, password):
        if user in self.pl.list:
            if program.principal == self.pl.list[user] or program.principal == self.pl.list["admin"]:
                self.pl.list[user].p = password # simple password hashing, pass plain
                return 2
            return 0
        return 1
    def set(self, program, parameter, expression):
        #print(" SET CALLED %s" % expression)
        if parameter in KEY_WORDS:
            return 1
        if parameter in self.ol:
            if program.principal.has_write(parameter):
                r,exp = self.expression(program, expression)
                if r == 2:
                    self.ol[parameter] = exp
                    return 2
                return r
            return 0
        elif parameter in program.local:
            r,exp = self.expression(program, expression)
            if r == 2:
                program.local[parameter] = exp
                return 2
            return r
        else:
            #print("SET CALLED %s" % expression)
            r,exp = self.expression(program, expression)
            #print(r)
            #print(exp)
            #print(parameter)
            if r == 2:
                self.ol[parameter] = exp
                #print(self.ol[parameter])
                #print("program.principal = %s" % program.principal.p)
                self.dm.add_delegation(parameter, self.pl.list["admin"], self.pl.list["admin"], "read")
                self.dm.add_delegation(parameter, self.pl.list["admin"], self.pl.list["admin"], "write")
                self.dm.add_delegation(parameter, self.pl.list["admin"], self.pl.list["admin"], "append")
                self.dm.add_delegation(parameter, self.pl.list["admin"], self.pl.list["admin"], "delegate")
                self.dm.add_delegation(parameter, self.pl.list["admin"], program.principal, "read")
                self.dm.add_delegation(parameter, self.pl.list["admin"], program.principal, "write")
                self.dm.add_delegation(parameter, self.pl.list["admin"], program.principal, "append")
                self.dm.add_delegation(parameter, self.pl.list["admin"], program.principal, "delegate")
                #print("END ADD_DELEGATIONS")
                return 2
            return r
        return 1

    def append(self, program, parameter, expression):
        #print("append called = %s,%s" % (parameter,expression))
        if parameter in self.ol:
            #print("param exists")
            if isinstance(self.ol[parameter], dict):
                #print("append global dict check")
                if program.principal.has_write(parameter) or program.principal.has_append(parameter):
                    #print("has_write/append check")
                    r,exp = self.expression(program, expression)
                    #print("r,exp = %s,%s" % (r,exp))
                    if r == 2:
                        try:
                            self.ol[parameter].update(exp)
                        except:
                            return 1
                        return 2
                    return r
                return 0
            elif isinstance(self.ol[parameter], list):
                #print("append list called")
                r,exp = self.expression(program, expression)
                #print("r,exp = %s,%s" % (r,exp))
                if r == 2:
                    exp = pickle.loads(pickle.dumps(exp))
                    if isinstance(exp, list):
                        self.ol[parameter].extend(exp)
                    else:
                        self.ol[parameter].append(exp)
                    #print("new list = %s" % self.ol[parameter])
                    return 2
                else:
                    return r
            elif isinstance(self.ol[parameter], str):
                pass
            else:
                return 1
        elif parameter in program.local:
            if isinstance(program.local[parameter], dict):
                r,exp = self.expression(program, expression)
                if r == 2:
                    try:
                        program.local[parameter].update(exp)
                    except:
                        return 1
                    return 2
                return r
            elif isinstance(self.ol[paramter], list):
                r,exp = self.expression(program, expression)
                if r == 2:
                    exp = pickle.loads(pickle.dumps(exp))
                    if isinstance(exp, list):
                        self.ol[parameter].extend(exp)
                    else:
                        self.ol[parameter].append(exp)
                else:
                    return r
            elif isinstance(self.ol[parameter], str):
                pass
            else:
                return 1
        return 1
    def local(self, program, parameter, expression):
        #print("local called = %s,%s" % (parameter, expression))
        if parameter not in program.local and parameter not in self.ol:
            #print("local param does not exists..create")
            r,exp = self.expression(program, expression)
            #print("r,exp = %s,%s" % (r,exp))
            if r == 2:
                program.local[parameter] = exp
                #print("new pl = %s,%s" % (program.local[parameter], parameter))
                return 2
            return r
        return 1
    def foreach(self, program, element, parameter, expression):
        '''
            `element` is the string value of variable name
            Check if `element` is in keywords and has read/write `<right>`
            Check if element is a local or global variable
            Check if value of key `element` is a dict
            Loop through and reassign each row in the `dict` to `expression`

        '''
        if element in self.ol or element in program.local:
            return 1
        #print("foreach called = %s,%s,%s" % (element, parameter, expression))
        if element not in KEY_WORDS and program.principal.has_read(parameter) and program.principal.has_write(parameter):
            #print("check 1 passed")
            if parameter in self.ol:
                #print("ol check 2 passed")
                if isinstance(self.ol[parameter], list): # It has to be a list..check doc for dic case?
                    #print("ol check 3 passed = %s" % self.ol[parameter])
                    new_list = []
                    for rec in self.ol[parameter]:
                        #print("rec = %s" % rec)
                        program.local[element] = rec
                        #print("for rec = %s" % rec)
                        if "{" in expression[0]:
                            #print("{} check. exp = %s" % expression)
                            r,exp = self.expression(program, expression)
                            #print("r,exp = %s,%s" % (r,expression))
                            if r == 2:
                                new_list.append(exp)
                            else:
                                return r
                        elif "." in expression:
                            key = expression.split(".")
                            key = key[1]
                            try:
                                rec = rec.get(key)
                                new_list.append(rec)
                            except:
                                #print("key does not exist")
                                del program.local[element]
                                return 1
                        del program.local[element]

                    self.ol[parameter] = new_list
                    #print("new list = %s" % self.ol[parameter])
            elif parameter in program.local:
                #print("loc check 2 passed ")
                if isinstance(program.local[parameter], list):
                    #print("loc check 3 passed = %s" % program.local[parameter])
                    new_list = []
                    for rec in program.local[parameter]:
                        program.local[element] = rec
                        #print("for rec = %s" % rec)
                        if "{" in expression[0]:
                            #print("{ elif check")
                            r,exp = self.expression(program, expression)
                            #print(" r,exp = %s,%s" % (r,exp))
                            if r == 2:
                                new_list.append(exp)
                            else:
                                return r
                        elif "." in expression:
                            key = expression.split(".")
                            key = key[1]
                            try:
                                rec = rec.get(key)
                                new_list.append(rec)
                            except:
                                #print("key does not exist")
                                del program.local[element]
                                return 1
                        del program.local[element]
                    program.local[parameter] = new_list
                    #print("new pl = %s" % program.local[parameter])
            else:
                return 1
            return 2
        return 0

    def set_delegation(self, program, target, delegator, permission, delegatee):
        if target == "all":
            if delegator in self.pl.list[delegator] and delegatee in self.pl.list[delegatee]:
                if program.principal == self.pl.list[delegator]:
                    delegations = self.pl.list[delegator].get_delegateable(self)
                    for d in delegations:
                        self.dm.add_delegation(d, self.pl.list[delegator], self.pl.list[delegatee], permission)
                    return 2
                return 0
        elif target in self.ol:
            #print("check -- target in self.ol")
            if delegator in self.pl.list and delegatee in self.pl.list:
                #print("check -- principal list")
                #if self.pl.list[delegator].has_delegation(target) and program.principal == self.pl.list[delegator]:
                #print("p, pl = %s,%s" % (program.principal, self.pl.list))
                #if program.principal == self.pl.list[delegator]:
                #print("check -- has_delegation and p.p=self.pl...")
                #print(" p1,p2, p3, p4 = %s,%s,%s,%s" % (target, self.pl.list[delegator], self.pl.list[delegatee], permission))
                self.dm.add_delegation(target, self.pl.list[delegator], self.pl.list[delegatee], permission)
                return 2
                return 0
        return 1
    def delete_delegation(self, program, target, delegator, permission, delegatee):
        if target == "all":
            if delegator in self.pl.list and delegatee in self.pl.list:
                if program.principal == self.pl.list[delegator]:
                    delegations = self.pl.list[delegator].get_delegateable(self)
                    for d in delegations:
                        self.dm.remove_delegation(d, self.pl.list[delegator], self.pl.list[delegatee], permission)
                    return 2
                return 0
        elif target in self.ol:
            if delegator in self.pl.list and delegatee in self.pl.list:
                if self.pl.list[delegator].has_delegation(target) and program.principal == self.pl.list[delegator]:
                    self.dm.remove_delegation(target, self.pl.list[delegator], self.pl.list[delegatee], permission)
                    return 2
                return 0
        return 1
    def default_delegator(self, program, delegator):
        #print("default_delegator = %s " % (delegator))
        if delegator in self.pl.list:
            #print("delegator pl check")
            if program.principal == self.pl.list["admin"]:
                #print("we are admin")
                self.dm.default = self.pl.list[delegator]
                #print("dm.default = %s" % self.dm.default)
                return 2
            return 0
        return 1
    def ret(self, program, expr):
        #def expression(self, program, expression):
        #print("def ret called")
        r,exp = self.expression(program, expr)
        if r == 2:
            #print("Return success = %s" % exp)
            return (2,exp)
        else:
            #print("Return Fail r=%s" % r)
            return (r,None) # DENIED or FAILURE
    def exit(self, program):
        if program.principal == self.pl.list["admin"]:
            connection_socket.send(status("EXITING").JSON() + "\n")
            return 2
        return 0
    def process_commands(self, program, sim):
        #output_status = []
        for index in program.queue:
            c = program.queue[index].lstrip()
            if "//" in c:
                c = c.split("//")
                c = c[0]
                #print(" // split = %s " % c)
            if c == "":
                #print("continue called")
                continue
            tmp_c = c.split(" ")
            tmp_c = filter(lambda x: x != "", tmp_c)

            #print("tmp_c=%s" % tmp_c)
            try:
                tmp_c[0] = tmp_c[0].lstrip()
                if tmp_c[0] == "as":
                #if re.search(PROG, c):
                    #print("re PROG")
                    pc = re.findall(PARSE_PROG, c)
                    r = self.program_begin(program, pc[0][0], pc[0][1])
                    if r == 1:
                        return 1
                    elif r == 0:
                        return 0
                elif tmp_c[0] == "exit":
                #elif re.search(EXIT, c):
                    #print("re EXIT_PRIN")
                    r = self.exit(program)
                    if sim == 1 and r == 2:
                        connection_socket.send(status("EXITING").JSON() + "\n")
                        exit(0)
                    else:
                        return r
                elif tmp_c[0] == "return":
                #elif re.search(RETURN, c):
                    #print("re RETURN_PRIN")
                    #pc = re.findall(PARSE_RETURN, c)
                    if len(tmp_c) == 2:
                        #print("tmp_c[1] == %s" % tmp_c[1])
                        r,exp = self.ret(program, tmp_c[1])
                        #print("WTF")
                    else:
                        return 1
                    #print("r = %s, exp = %s" % (r,exp))
                    if sim == 1 and r == 2:
                        #print("exp = %s" % exp)
                        #print(type(exp))
                        # list, dict, string
                        # tmp_c = filter(lambda x: x != "", tmp_c)
                        if isinstance(exp, list):
                            #print("list return instance")
                            new_exp = []
                            i = 0
                            for rec in exp:
                                if isinstance(rec, str):
                                    #print("string found")
                                    rec = rec.lstrip()
                                    rec = rec.rstrip()
                                    #print("rec = %s" % rec)
                                    if rec[0] == "\"" and rec[-1] == "\"":
                                        rec = rec[1:-1]
                                    exp[i] = rec
                                    i += 1
                                    #new_exp.append(rec)
                                    #print("rec = %s" % rec)
                                elif isinstance(rec, dict):
                                    #print("dict found")
                                    tmp_dict = {}
                                    for key in rec:
                                        if isinstance(rec[key], str):
                                            if rec[key][0] == "\"" and rec[key][-1] == "\"":
                                                rec[key] = rec[key][1:-1]
                                            tmp_dict[key] = rec[key]
                                        #print("key,value = %s,%s" % (key, rec[key]))
                                    exp[i] = rec
                                    i += 1

                            #print("new exp = %s" % new_exp)

                        elif isinstance(exp, dict):
                            for key in exp:
                                if isinstance(exp[key], str):
                                    if exp[key][0] == "\"" and exp[key][-1] == "\"":
                                        exp[key] = exp[key][1:-1]
                        elif isinstance(exp, str):
                            #print("str match")
                            if exp[0] == "\"" and exp[-1] == "\"":
                                exp = exp[1:-1]
                        else:
                            #print("Unexpected Type in def process--return()")
                            return 1
                        connection_socket.send(status("RETURNING", exp).JSON() + "\n")
                    elif r != 2:
                        #print("sim = %s, r = %s" % (sim,r))
                        return r
                elif tmp_c[0] == "***":
                #elif re.search(TERMIN, c):
                    return 2
                elif tmp_c[0] == "create":
                #elif re.search(CREATE_PRIN, c):
                    #print("re CREATE_PRIN")
                    pc = re.findall(PARSE_CREATE, c)
                    #print("findall = %s" % pc)
                    r = self.create_principal(program, pc[0][0], pc[0][1])
                    #print("sim = %s, r=%s" % (sim,r))
                    if sim == 1 and r == 2:
                        connection_socket.send(status("CREATE_PRINCIPAL").JSON() + "\n")
                    elif r != 2:
                        return r
                elif tmp_c[0] == "change":
                #elif re.search(CHANGE_PRIN, c):
                    #print("re CHANGE_PRIN")
                    pc = re.findall(PARSE_CHANGE, c)
                    r = self.change_password(program, pc[0][0], pc[0][1])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("CHANGE_PASSWORD").JSON() + "\n")
                    elif r != 2:
                        return r
                elif ' '.join(tmp_c[0:2]) == "set delegation":
                #elif re.search(SET_DEL, c):
                    #print("re SET_DEL")
                    pc = re.findall(PARSE_SET_DEL, c)
                    r = self.set_delegation(program, pc[0][0], pc[0][1], pc[0][2], pc[0][3])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("SET_DELEGATION").JSON() + "\n")
                    elif r != 2:
                        return r
                elif ' '.join(tmp_c[0:2]) == "delete delegation":
                #elif re.search(DEL_DEL, c):
                    #print("re DEL_DEL")
                    pc = re.findall(PARSE_DEL_DEL, c)
                    r = self.delete_delegation(program, pc[0][0], pc[0][1], pc[0][2], pc[0][3])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("DELETE_DELEGATION").JSON() + "\n")
                    elif r != 2:
                        return r
                elif tmp_c[0] == "set":
                #elif re.search(SET, c):
                    #print("re PARSE_SET")
                    pc = re.findall(PARSE_SET, c)
                    r = self.set(program, pc[0][0], pc[0][1])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("SET").JSON() + "\n")
                    elif r != 2:
                        return r
                elif tmp_c[0] == "append":
                #elif re.search(APPEND, c):
                    #print("re APPEND")
                    pc = re.findall(PARSE_APPEND, c)
                    r = self.append(program, pc[0][0], pc[0][1])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("APPEND").JSON() + "\n")
                    elif r != 2:
                        return r
                elif tmp_c[0] == "local":
                #elif re.search(LOCAL, c):
                    #print("re LOCAL")
                    pc = re.findall(PARSE_LOCAL, c)
                    r = self.local(program, pc[0][0], pc[0][1])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("LOCAL").JSON() + "\n")
                    elif r != 2:
                        return r
                elif tmp_c[0] == "foreach":
                #elif re.search(FOREACH, c):
                    #print("re FOREACH")
                    pc = re.findall(PARSE_FOREACH, c)
                    #print("pc = %s" % pc[0][2])
                    r = self.foreach(program, pc[0][0], pc[0][1], pc[0][2])
                    #print("r = %s" % r)
                    if sim == 1 and r == 2:
                        connection_socket.send(status("FOREACH").JSON() + "\n")
                    elif r != 2:
                        return r
                elif ' '.join(tmp_c[0:2]) == "default delegator":
                #elif re.search(DEF_DEL, c):
                    #print("re DEF_DEL")
                    pc = re.findall(PARSE_DEF_DEL, c)
                    #print("pc = %s" % pc)
                    r = self.default_delegator(program, pc[0])
                    if sim == 1 and r == 2:
                        connection_socket.send(status("DEFAULT_DELEGATOR").JSON() + "\n")
                    elif r != 2:
                        return r
                else:
                    return 1
            except IndexError, e:
                #print("Error 1")
                return 1
            except TypeError, e:
                #print("Error 0")
                return 1
            except KeyError, e:
                #print("Error 1-3")
                return 1
            except RuntimeError, e:
                return 1
        return 2

def BiBiFi(port, password):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.settimeout(30)
    try:
        s.bind(('',port))
    except socket.error, e:
        exit(63)
    s.listen(0)
    l = lexer(password)
    while 1:
        #print("while")
        try:
            p = program()
            global connection_socket
            connection_socket, connection_address = s.accept()
            #connection_socket.settimeout(30)
            while 1:
                #print("while2")
                #print("c=%s" % c)
                temp_c = ""
                c = ""
                while temp_c.find("***") == -1:
                    temp_c = connection_socket.recv(4096)
                    c += temp_c
                sp = c.split("\n")
                #print("sp = %s" % sp)
                for x in sp:
                    p.queue[len(p.queue)] = x.replace("\r","")
                if "***" in p.queue.values(): # Think about
                    #print("p.queue = %s" % p.queue)
                    p.queue = {k: v for k, v in p.queue.items() if v is not ''}
                    #print("filtered p.queue = %s" % p.queue)
                    #sys.setrecursionlimit(15000)
                    sl = copy.deepcopy(l)
                    r = sl.process_commands(p,0)
                    #print("sim r = %s" % r)
                    if r == 2:
                        p.principal = None
                        p.local = {}
                        l.process_commands(p,1)
                    elif r == 1:
                        connection_socket.send(status("FAILED").JSON() + "\n")
                    else:
                        connection_socket.send(status("DENIED").JSON() + "\n")
                    break
            connection_socket.close();
        except socket.error, e:
            connection_socket.send(status("TIMEOUT").JSON() + "\n")
            connection_socket.close();
        except IOError, e:
            connection_socket.send(status("FAILED").JSON() + "\n")
            #print("unknown IO problem")
            connection_socket.close();
        except KeyboardInterrupt, e:
            exit(0)
        except RuntimeError, e:
            connection_socket.send(status("FAILED").JSON() + "\n")
            connection_socket.close();

def main():
    if len(sys.argv) > 1:
        if str(sys.argv[1])[0] == "0" or str(sys.argv[1]).find(" ") != -1:
            exit(255)
        port = int(sys.argv[1])
        password = ""
        signal.signal(signal.SIGTERM, sigterm_handler)
        if len(sys.argv) > 2:
            password = sys.argv[2]
        if port >= 1024 and port <= 65535:
            BiBiFi(port, password)
    exit(255)

if __name__ == "__main__":
    main()
