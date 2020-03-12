import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import Database
from parser.parser import parse


def validate_tests(d, tests):
    for test in tests:
        ret = parse(d, test["text"])
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]
        if "output" in test:
            if isinstance(test["output"], list):
                for first, second in zip(test["output"], ret[-1]["output"]):
                    if isinstance(first, dict):
                        for k in first:
                            assert k in second
                            assert first[k] == second[k]
                    else:
                        assert first == second
            elif isinstance(test["output"], dict):
                for k in ret[-1]["output"]:
                    assert k in test["output"]
                    assert ret[-1]["output"][k] == test["output"][k] 
            assert ret[-1]["output"] == test["output"]
        else:
            assert "output" not in ret[-1]
        d.reset()


class Test_Basic_Parse:

    def test_basic_parse(self):
        d = Database("admin")

        text = 'as principal admin password "admin" do\ncreate principal bob "BOBPWxxd"\nset x="my string"\nset y = { f1 = x, f2 = "field2" }\nset delegation x admin read -> bob\nreturn y.f1\n***'

        tests = [
            {
                "text": text,
                "exp_status": ["CREATE_PRINCIPAL", "SET", "SET", "SET_DELEGATION", "RETURNING"],
                "output": "my string"
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)
    
    def test_mult_commands(self):
        d = Database("admin")

        text1 = 'as principal admin password "admin" do\ncreate principal bob "password"\ncreate principal alice "password"\nset x="this is a string"\nset delegation all admin delegate->bob\nset delegation all admin read->bob\nreturn x\n***'
        text2 = 'as principal bob password "password" do\nset y="another record"\nset delegation all bob read->alice\nreturn y\n***'
        text3 = 'as principal alice password "password" do\nreturn x\n***'
        text4 = 'as principal alice password "password" do\nreturn y\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["CREATE_PRINCIPAL", "CREATE_PRINCIPAL", "SET", "SET_DELEGATION", "SET_DELEGATION", "RETURNING"],
                "output": "this is a string"
            },
            {
                "text": text2,
                "exp_status": ["SET", "SET_DELEGATION", "RETURNING"],
                "output": "another record"
            },
            {
                "text": text3,
                "exp_status": ["RETURNING"],
                "output": "this is a string"
            },
            {
                "text": text4,
                "exp_status": ["RETURNING"],
                "output": "another record"
            },
        ]

        d = Database("admin")

        validate_tests(d, tests)


class Test_Exit_Parse:
    
    def test_exit_properly(self):
        text1 = 'as principal admin password "admin" do\nexit\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["EXITING"]
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)

    def test_exit_fails(self):
        text1 = 'as principal admin password "admin" do\ncreate principal bob "password"\nexit\n***'
        text2 = 'as principal bob password "password" do\nexit\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["CREATE_PRINCIPAL", "EXITING"]
            },
            {
                "text": text2,
                "exp_status": ["DENIED"]
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)


class Test_Return_Parse:
    
    def test_return_elem(self):
        text1 = 'as principal admin password "admin" do\nset x = "elem"\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "RETURNING"],
                "output": "elem"
            },
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_return_record(self):
        text1 = 'as principal admin password "admin" do\n set x = {field1="element", field2="element"}\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "RETURNING"],
                "output": {"field1": "element", "field2": "element"}
            },
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_return_record_field(self):
        text1 = 'as principal admin password "admin" do\n set x ={first="jonathan", last="innis"}\nreturn x.last\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "RETURNING"],
                "output": "innis"
            },
        ]

        d = Database("admin")
        
        validate_tests(d, tests)


class Test_Auth_Parse:

    def test_valid_auth(self):
        text1 = 'as principal admin password "admin" do\ncreate principal bob "password1"\ncreate principal alice "password2"\ncreate principal eve "password3"\nreturn "exiting"\n***'
        text2 = 'as principal bob password "password1" do\nreturn "exiting"\n***'
        text3 = 'as principal alice password "password2" do\nreturn "exiting"\n***'
        text4 = 'as principal eve password "password3" do\nreturn "exiting"\n***'
        text5 = 'as principal bob password "sfoasjfoidsafiosja43589289" do\nreturn "exiting"\n***'
        text6 = 'as principal admin password "admin1" do\nreturn "exiting"\n***'
        text7 = 'as principal admin password "admi" do\nreturn "exiting"\n***'
        text8 = 'as principal bobby password "password3" do\nreturn "exiting"\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["CREATE_PRINCIPAL", "CREATE_PRINCIPAL", "CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text2,
                "exp_status": ["RETURNING"],
                "output": "exiting"
            },
            {
                "text": text3,
                "exp_status": ["RETURNING"],
                "output": "exiting"
            },
            {
                "text": text4,
                "exp_status": ["RETURNING"],
                "output": "exiting"
            },
            {
                "text": text5,
                "exp_status": ["DENIED"],
            },
            {
                "text": text6,
                "exp_status": ["DENIED"],
            },
            {
                "text": text7,
                "exp_status": ["DENIED"],
            },
            {
                "text": text8,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_require_auth(self):
        text1 = 'create principal bob "password1"\nexit\n***'
        text2 = 'set x =[]\nexit\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"],
            },
            {
                "text": text2,
                "exp_status": ["FAILED"],
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)


class Test_Append_Parse:

    def test_append_list(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset y =[]\nset z={first= "elem", second= "elem"}\nappend to x with "str"\n append to y with z\n append to y with z\nappend to x with y\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "SET", "SET", "APPEND", "APPEND", "APPEND", "APPEND", "RETURNING"],
                "output": ["str", {"first": "elem", "second": "elem"}, {"first": "elem", "second": "elem"}]
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_append_str(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset z="str"\nappend to x with z\n append to x with z\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "SET", "APPEND", "APPEND", "RETURNING"],
                "output": ["str", "str"]
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_append_dict(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset z={first="elem", second="elem"}\nappend to x with z\n append to x with z\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "SET", "APPEND", "APPEND", "RETURNING"],
                "output": [{"first": "elem", "second": "elem"}, {"first": "elem", "second": "elem"}]
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

class Test_Whitespace_Parse:
    
    def test_valid_whitespace(self):
        text1 = '    as      principal      admin       password      "admin"       do\n   set    x    =    "this is a string"    \n       return       x    \n     ***   '
        text2 = 'as principal admin password "admin" do\n     set     x     =    {       x      =     "elem"     ,     name      =      "jonny"     }    \n      return   x     .      x    \n    ***   '
        text3 = 'as principal admin password "admin" do\n      set      x       =[]       \n        return      x   \n    ***      '
        text4 = 'as principal admin password "admin" do\n      create      principal       jonny      "password"    \n return "exiting"\n ***'
        text5 = 'as principal admin password "admin" do\n        change       password      admin        "another password"     \n        return       "exiting"     \n      ***     '
        text6 = 'as principal admin password "another password" do\nset x=[]\n        append      to      x       with       {x="elem",name="anotherelem"}      \n        return        x       \n     ***     '
        text7 = 'as principal admin password "another password" do\n         local          y         =           "elem"       \n        return       y      \n     ***      '
        text8 = 'as principal admin password "another password" do\n        foreach        rec        in        x        replacewith       rec.x      \n       return      x      \n      ***      '
        text9 = 'as principal admin password "another password" do\n      set        delegation      x      admin        read        ->      jonny       \n     return            "exiting"       \n       ***      '
        text10 = 'as principal admin password "another password" do\n     delete         delegation       x          admin       read       ->          jonny       \n           return         "exiting"       \n       ***     '
        text11 = 'as principal admin password "another password" do\n        default         delegator       =        admin        \n          return         "exiting"        \n       ***     '
        text12 = 'as principal admin password "another password" do\n         set            z               =                     []            \n          append       to      z       with         "expression"   \n        append  to  z   with      "another expression"       \n        return z    \n   ***   '

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "RETURNING"],
                "output": "this is a string"
            },
            {
                "text": text2,
                "exp_status": ["SET", "RETURNING"],
                "output": "elem"
            },
            {
                "text": text3,
                "exp_status": ["SET", "RETURNING"],
                "output": []
            },
            {
                "text": text4,
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text5,
                "exp_status": ["CHANGE_PASSWORD", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text6,
                "exp_status": ["SET", "APPEND", "RETURNING"],
                "output": [{"x": "elem", "name": "anotherelem"}]
            },
            {
                "text": text7,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": "elem"
            },
            {
                "text": text8,
                "exp_status": ["FOREACH", "RETURNING"],
                "output": ["elem"]
            },
            {
                "text": text9,
                "exp_status": ["SET_DELEGATION", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text10,
                "exp_status": ["DELETE_DELEGATION", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text11,
                "exp_status": ["DEFAULT_DELEGATOR", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text12,
                "exp_status": ["SET", "APPEND", "APPEND", "RETURNING"],
                "output": ["expression", "another expression"]
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_auth(self):
        text1 = 'asprincipal admin password "admin" do\nreturn ""\n***'
        text2 = 'as principaladmin password "admin" do\nreturn ""\n***'
        text3 = 'as principal adminpassword "admin" do\nreturn ""\n***'
        text4 = 'as principal admin password"admin" do\nreturn ""\n***'
        
        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            },
            {
                "text": text4,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_return(self):
        text1 = 'as principal admin password "admin" do\nreturn[]\n***'
        text2 = 'as principal admin password "admin" do\nreturn""\n***'
        text3 = 'as principal admin password "admin" do\nreturn{}\n***'
        
        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_create_principal(self):
        text1 = 'as principal admin password "admin" do\ncreateprincipal bobby "password"\nreturn ""\n***'
        text2 = 'as principal admin password "admin" do\ncreate principalbobby "password"\nreturn ""\n***'
        text3 = 'as principal admin password "admin" do\ncreate principal bobby"password"\nreturn ""\n***'
        
        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_change_password(self):
        text1 = 'as principal admin password "admin" do\nchangepassword admin "password"\nreturn ""\n***'
        text2 = 'as principal admin password "admin" do\nchange passwordadmin "password"\nreturn ""\n***'
        text3 = 'as principal admin password "admin" do\nchange password admin"password"\nreturn ""\n***'


        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_set(self):
        text1 = 'as principal admin password "admin" do\nsetx=""\nreturn x\n***'
        text2 = 'as principal admin password "admin" do\nset x=""\nreturn x\n***'
        text3 = 'as principal admin password "admin" do\nset x={y=x}\nreturn x\n***'
        text4 = 'as principal admin password "admin" do\nset x=[]\nreturn x\n***'
        text5 = 'as principal admin password "admin" do\nset x={y="another_elem",z="elem"}\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["SET", "RETURNING"],
                "output": ""
            },
            {
                "text": text3,
                "exp_status": ["SET", "RETURNING"],
                "output": {"y": ""}
            },
            {
                "text": text4,
                "exp_status": ["SET", "RETURNING"],
                "output": []
            },
            {
                "text": text5,
                "exp_status": ["SET", "RETURNING"],
                "output": {"y": "another_elem", "z": "elem"}
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)

    def test_invalid_append(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nappendto x with "element"\nreturn x\n***'
        text2 = 'as principal admin password "admin" do\nset x=[]\nappend tox with "element"\nreturn x\n***'
        text3 = 'as principal admin password "admin" do\nset x=[]\nappend to xwith "element"\nreturn x\n***'
        text4 = 'as principal admin password "admin" do\nset x=[]\nappend to x with"element"\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            },
            {
                "text": text4,
                "exp_status": ["FAILED"]
            },
        ]

        d = Database("admin")
        validate_tests(d, tests)

    def test_invalid_local(self):
        text1 = 'as principal admin password "admin" do\nlocalx=""\nreturn x\n***'
        text2 = 'as principal admin password "admin" do\nlocal x=""\nreturn x\n***'
        text3 = 'as principal admin password "admin" do\nlocal x={y="elem"}\nreturn x\n***'
        text4 = 'as principal admin password "admin" do\nlocal x=[]\nreturn x\n***'
        text5 = 'as principal admin password "admin" do\nlocal x={y="another_elem",z="elem"}\nreturn x\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"]
            },
            {
                "text": text2,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": ""
            },
            {
                "text": text3,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": {"y": "elem"}
            },
            {
                "text": text4,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": []
            },
            {
                "text": text5,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": {"y": "another_elem", "z": "elem"}
            }
        ]

        d = Database("admin")

        validate_tests(d, tests)


class Test_Comments:

    def test_valid_comment(self):
        text1 = 'as principal admin password "admin" do //this is a comment\nreturn "returning"\n***'
        text2 = 'as principal admin password "admin" do//this is a comment\nreturn "returning"\n***'
        text3 = 'as principal admin password "admin" do\n// this is a full line comment that I want removed\nreturn "returning"\n***'
        text4 = 'as principal admin password "admin" do\n    // this is an invalid full line comment\nreturn "returning"\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["RETURNING"],
                "output": "returning"
            },
            {
                "text": text2,
                "exp_status": ["RETURNING"],
                "output": "returning"
            },
            {
                "text": text3,
                "exp_status": ["RETURNING"],
                "output": "returning"
            },
            {
                "text": text4,
                "exp_status": ["FAILED"],
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)


class Test_Failed_Parse:

    def test_read_invalid_field(self):
        text1 = 'as principal admin password "admin" do\nset x="element"\nreturn x.y\n***'
        text2 = 'as principal admin password "admin" do\nset x=[]\nappend to x with "str"\nreturn x.elem\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"],
            },
            {
                "text": text2,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)