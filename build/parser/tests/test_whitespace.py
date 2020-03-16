from db.database import Database
from parser.parser import Parser

def validate_tests(d, tests):
    p = Parser()
    for test in tests:
        ret = p.parse(d, test["text"])
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
