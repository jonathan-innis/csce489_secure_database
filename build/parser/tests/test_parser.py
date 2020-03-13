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
        text3 = 'change password admin "password"\nexit\n***'
        text4 = 'set x = []\nappend to x with "str"\nexit\n***'
        text5 = 'local x = "str"\nexit\n***'
        text6 = 'set x = []\nappend to x with {first="jonathan", last="innis"}\nappend to x with {first="reuben", second="tadpatri"}\nforeach rec in x replacewith rec.first\nexit\n***'
        text7 = 'as principal admin password "admin" do\ncreate principal bobby "pasword"\nset x = "str"\nreturn x\n***'
        text8 = 'set delegation x admin read -> bobby\nexit\n***'
        text9 = 'delete delegation x admin read -> bobby\nexit\n***'
        text10 = 'default delegator = admin\nexit\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["FAILED"],
            },
            {
                "text": text2,
                "exp_status": ["FAILED"],
            },
            {
                "text": text3,
                "exp_status": ["FAILED"],
            },
            {
                "text": text4,
                "exp_status": ["FAILED"],
            },
            {
                "text": text5,
                "exp_status": ["FAILED"],
            },
            {
                "text": text6,
                "exp_status": ["FAILED"],
            },
            {
                "text": text7,
                "exp_status": ["CREATE_PRINCIPAL", "SET", "RETURNING"],
                "output": "str"
            },
            {
                "text": text8,
                "exp_status": ["FAILED"],
            },
            {
                "text": text9,
                "exp_status": ["FAILED"],
            },
            {
                "text": text10,
                "exp_status": ["FAILED"],
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)


class Test_Create_Principal:

    def test_valid_create_principal(self):
        text1 = 'as principal admin password "admin" do\ncreate principal bob "password"\nreturn "exiting"\n***'
        text2 = 'as principal admin password "admin" do\ncreate principal alice "qu984u 2u08f9a0fu0sa9d8"\nreturn "exiting"\n***'
        text3 = 'as principal admin password "admin" do\ncreate principal eve "return"\nreturn "exiting"\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text2,
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text3,
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)

    def test_invalid_create_principal(self):
        text1 = 'as principal admin password "admin" do\ncreate principal bob\nreturn "exiting"\n***' # malformed command
        text2 = 'as principal admin password "admin" do\ncreate principal bob password\nreturn "exiting"\n***' # malformed command
        text3 = 'as principal admin password "admin" do\ncreate principal bob "password"\nreturn "exiting"\n***' # valid command
        text4 = 'as principal bob password "password" do\ncreate principal alice "password"\nreturn "exiting"\n***' # non-admin creating principal
        text5 = 'as principal admin password "admin" do\ncreate principal bob "anotherpassword"\nreturn "exiting"\n***' # creating a duplicate user
        text6 = 'as principal admin password "admin" do\ncreate principal principal "password"\nreturn "exiting"\n***' # using a reserved keyword
        text7 = 'as principal admin password "admin" do\ncreate principal anyone "password"\nreturn "exiting"\n***' # trying to create user anyone
        text8 = 'as principal admin password "admin" do\ncreate principal admin "password"\nreturn "exiting"\n***' # trying to create a new admin user

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
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text4,
                "exp_status": ["DENIED"]
            },
            {
                "text": text5,
                "exp_status": ["FAILED"]
            },
            {
                "text": text6,
                "exp_status": ["FAILED"]
            },
            {
                "text": text7,
                "exp_status": ["FAILED"]
            },
            {
                "text": text8,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)


class Test_Change_Password:

    def test_valid_change_password(self):
        text1 = 'as principal admin password "admin" do\nchange password admin "another password"\nreturn "exiting"\n***' # valid password change of admin
        text2 = 'as principal admin password "admin" do\nreturn "exiting"\n***' # invalid password because of change
        text3 = 'as principal admin password "another password" do\ncreate principal bob "password"\nreturn "exiting"\n***' # valid authentication and created principal
        text4 = 'as principal bob password "password" do\nchange password bob "this is a longer password and im using this password"\nreturn "exiting"\n***' # valid password change
        text5 = 'as principal bob password "this is a longer password and im using this password" do\nchange password admin "iknowthepassword"\nreturn "exiting"\n***' # invlaid admin password change
        text6 = 'as principal admin password "another password" do\nchange password bob "originalpassword"\nreturn "exiting"\n***' # admin changes another user password
        text7 = 'as principal bob password "this is a longer password and im using this password" do\nreturn "exiting"\n***' # invalid password because of change
        text8 = 'as principal bob password "originalpassword" do\nreturn "exiting"\n***' # valid password
        text9 = 'as principal admin password "another password" do\nchange password alice "password"\nreturn "exiting"\n***' # principal doesn't exist
        text10 = 'as principal admin password "another password" do\nchange password anyone "differentpassword"\nreturn "exiting"\n***' # shouldn't be able to change anyone

        tests = [
            {
                "text": text1,
                "exp_status": ["CHANGE_PASSWORD", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text2,
                "exp_status": ["DENIED"]
            },
            {
                "text": text3,
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text4,
                "exp_status": ["CHANGE_PASSWORD", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text5,
                "exp_status": ["DENIED"],
            },
            {
                "text": text6,
                "exp_status": ["CHANGE_PASSWORD", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text7,
                "exp_status": ["DENIED"],
            },
            {
                "text": text8,
                "exp_status": ["RETURNING"],
                "output": "exiting"
            },
            {
                "text": text9,
                "exp_status": ["FAILED"],
            },
            {
                "text": text10,
                "exp_status": ["DENIED"] #TODO: check if this is the right return status for this kind of error
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)


class Test_Set:

    def test_valid_set(self):
        text1 = 'as principal admin password "admin" do\nset x = "hello"\nset y = x\nset x = "there"\nreturn y\n***' # Check that elements are deepcopied
        text2 = 'as principal admin password "admin" do\nreturn x\n***' # Also checks that element is deepcopied
        text3 = 'as principal admin password "admin" do\nset x = {elem1=[]}\nreturn x\n***' # Ensures this is invalid
        text4 = 'as principal admin password "admin" do\nset x = {elem1={innerelem="str"}}\nreturn x\n***' # Ensures this is invalid
        text5 = 'as principal admin password "admin" do\nset x = {f1 = "field"}\ncreate principal alice "password"\nreturn x\n***' # Creates an element and principal
        text6 = 'as principal alice password "password" do\nset z = {f1=x.f2, f2=x.f1}\nreturn z\n***' # Ensures that permission is read before field existence is checked
        text7 = 'as principal alice password "password" do\nset z = {f1=aa, f1=x.f1}\nreturn z\n***' # Ensures that elements are evaluated left to right
        text8 = 'as principal admin password "admin" do\nset delegation x admin read -> alice\nreturn "exiting"\n***' # Gives permission for principal to read record now
        text9 = 'as principal alice password "password" do\nset z = {f1=x}\nreturn z\n***' # Ensures this is invalid
        text10 = 'as principal alice password "password" do\nset z = {f1=x.f1}\nreturn z\n***' # Ensures that principal can now set element
        text11 = 'as principal alice password "password" do\nset aa = {f1=x.f1, f2=x.f2}\nreturn aa\n***' # Ensures that field existence is still checked
        text12 = 'as principal alice password "password" do\nset principal = "str"\nreturn principal\n***' # Ensures reserved keywords
        text13 = 'as principal alice password "password" do\nset as = "str"\nreturn as\n***' # Ensures reserved keywords
        text14 = 'as principal alice password "password" do\nset password = "str"\nreturn password\n***' # Ensures reserved keywords
        text15 = 'as principal alice password "password" do\nset i = []\nappend to i with "one"\nappend to i with "two"\nset j = i\nappend to i with "three"\nreturn i\n***' # Check that elements are deepcopied
        text16 = 'as principal alice password "password" do\nreturn j\n***' # Also checks that element is deepcopied   

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "SET", "SET", "RETURNING"],
                "output": "hello"
            },
            {
                "text": text2,
                "exp_status": ["RETURNING"],
                "output": "there"
            },
            {
                "text": text3,
                "exp_status": ["FAILED"]
            },
            {
                "text": text4,
                "exp_status": ["FAILED"]
            },
            {
                "text": text5,
                "exp_status": ["SET", "CREATE_PRINCIPAL", "RETURNING"],
                "output": {
                    "f1": "field"
                }
            },
            {
                "text": text6,
                "exp_status": ["DENIED"]
            },
            {
                "text": text7,
                "exp_status": ["FAILED"]
            },
            {
                "text": text8,
                "exp_status": ["SET_DELEGATION", "RETURNING"],
                "output": "exiting"
            },
            {
                "text": text9,
                "exp_status": ["FAILED"]
            },
            {
                "text": text10,
                "exp_status": ["SET", "RETURNING"],
                "output": {
                    "f1": "field"
                }
            },
            {
                "text": text11,
                "exp_status": ["FAILED"]
            },
            {
                "text": text12,
                "exp_status": ["FAILED"]
            },
            {
                "text": text13,
                "exp_status": ["FAILED"]
            },
            {
                "text": text14,
                "exp_status": ["FAILED"]
            },
            {
                "text": text15,
                "exp_status": ["SET", "APPEND", "APPEND", "SET", "APPEND", "RETURNING"],
                "output": ["one", "two", "three"]
            },
            {
                "text": text16,
                "exp_status": ["RETURNING"],
                "output": ["one", "two"]
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)

class Test_Append:

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


class Test_Local:

    def test_valid_local(self):
        text1 = 'as principal admin password "admin" do\ncreate principal alice "password"\nlocal x = "element"\nreturn x\n***'
        text2 = 'as principal alice password "password" do\nset x = "anotherelement"\nreturn x\n***'
        text3 = 'as principal admin password "admin" do\nlocal y = "hello"\nreturn y\n***'
        text4 = 'as principal alice password "password" do\nlocal y = "there"\nreturn y\n***'
        text5 = 'as principal alice password "password" do\nlocal x = []\nreturn x'
        text6 = 'as principal admin password "admin" do\nset var = "my_element"\nreturn var\n***'
        text7 = 'as principal alice password "admin" do\nreturn var\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["CREATE_PRINCIPAL", "LOCAL", "RETURNING"],
                "output": "element"
            },
            {
                "text": text2,
                "exp_status": ["SET", "RETURNING"],
                "output": "anotherelement"
            },
            {
                "text": text3,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": "hello"
            },
            {
                "text": text4,
                "exp_status": ["LOCAL", "RETURNING"],
                "output": "there"
            },
            {
                "text": text5,
                "exp_status": ["FAILED"]
            },
            {
                "text": text6,
                "exp_status": ["SET", "RETURNING"],
                "output": "my_element"
            },
            {
                "text": text7,
                "exp_status": ["DENIED"]
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
            {# changes the password of principal if the principal isn't "anyone"
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


class Test_String_Functions:

    def test_valid_string_function(self):
        text1 = 'as principal admin password "admin" do\nlocal x = "hello"\nlocal y = split(x,"--")\nlocal z = concat(x,y.fst)\nreturn { x=x,y=y.snd,z=z }\n***'
        text2 = 'as principal admin password "admin" do\nlocal x = "BIGWORD"\n local y = tolower(x)\nreturn y\n***'
        text3 = 'as principal admin password "admin" do\nlocal x = {f1 = "hello", f2 = "there"}\nlocal y = concat(x.f1, " ")\nset y = concat(y, x.f2)\nreturn y\n***'
        text4 = 'as principal admin password "admin" do\nlocal x = "BIGWORD"\nlocal s = "---"\nlocal y = split(x, s)\nlocal aa = tolower(y.fst)\nlocal ab = tolower(y.snd)\nlocal z = {fst=aa, snd=ab}\nreturn z\n***'
        text5 = 'as principal admin password "admin" do\nlocal x = "element"\nlocal y = "element"\n local z = equal(x,y)\nreturn z\n***'
        text6 = 'as principal admin password "admin" do\nlocal x = "element"\nlocal y = "element"\nlocal z = notequal(x,y)\nreturn z\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["LOCAL", "LOCAL", "LOCAL", "RETURNING"],
                "output": {
                    "z": "hellohe",
                    "x": "hello",
                    "y": "llo"
                }
            },
            {
                "text": text2,
                "exp_status": ["LOCAL", "LOCAL", "RETURNING"],
                "output": "bigword"
            },
            {
                "text": text3,
                "exp_status": ["LOCAL", "LOCAL", "SET", "RETURNING"],
                "output": "hello there"
            },
            {
                "text": text4,
                "exp_status": ["LOCAL", "LOCAL", "LOCAL", "LOCAL", "LOCAL", "LOCAL", "RETURNING"],
                "output": {
                    "fst": "big",
                    "snd": "word"
                }
            },
            {
                "text": text5,
                "exp_status": ["LOCAL", "LOCAL", "LOCAL", "RETURNING"],
                "output": ""
            },
            {
                "text": text6,
                "exp_status": ["LOCAL", "LOCAL", "LOCAL", "RETURNING"],
                "output": "0"
            }
        ]

        d = Database("admin")
        
        validate_tests(d, tests)

    def test_invalid_arguments(self):
        text1 = 'as principal admin password "admin" do\nset x = tolower()\nreturn x\n***'
        text2 = 'as principal admin password "admin" do\nset x = tolower("element", "anotherelement")\nreturn x\n***'
        text3 = 'as principal admin password "admin" do\nset x = concat("hello")\nreturn x\n***'
        text4 = 'as principal admin password "admin" do\nset x = concat("hello", " ", "there")\nreturn x\n***'
        text5 = 'as principal admin password "admin" do\nset x = split("hello")\nreturn x\n***'
        text6 = 'as principal admin password "admin" do\nset x = split("hello", "--", "-")\nreturn x\n***'

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
            {
                "text": text5,
                "exp_status": ["FAILED"]
            },
            {
                "text": text6,
                "exp_status": ["FAILED"]
            }
        ]

        d = Database("admin")
        validate_tests(d, tests)


class Test_Filtereach:

    def test_ritchey_example(self):
        text1 = 'as principal admin password "admin" do\nset records=[]\nappend to records with { name = "mike", date = "1-1-90" }\nappend to records with { name = "sandy", date = "1-1-90" }\nappend to records with { name = "dave", date = "1-1-85" }\nfiltereach rec in records with equal(rec.date,"1-1-90")\nreturn records\n***'

        tests = [
            {
                "text": text1,
                "exp_status": ["SET", "APPEND", "APPEND", "APPEND", "FILTEREACH", "RETURNING"],
                "output": [
                    {
                        "date": "1-1-90",
                        "name": "mike"
                    },
                    {
                        "date": "1-1-90",
                        "name": "sandy"
                    }
                ]
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