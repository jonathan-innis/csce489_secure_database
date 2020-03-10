import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import Database
from parser.parser import parse


class Test_Basic_Parse:

    def test_basic_parse(self):
        d = Database("admin")

        text = 'as principal admin password "admin" do\ncreate principal bob "BOBPWxxd"\nset x="my string"\nset y = { f1 = x, f2 = "field2" }\nset delegation x admin read -> bob\nreturn y.f1\n***'
        ret = parse(d, text)

        exp_status = ["CREATE_PRINCIPAL", "SET", "SET", "SET_DELEGATION", "RETURNING"]

        assert len(ret) == len(exp_status)
        for i, elem in enumerate(ret):
            assert elem["status"] == exp_status[i]

        assert ret[-1]["output"] == "my string"
    
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
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]
            assert ret[-1]["output"] == test["output"]


class Test_Exit_Parse:
    
    def test_exit_properly(self):
        text1 = 'as principal admin password "admin" do\nexit\n***'

        test = {
                "text": text1,
                "exp_status": ["EXITING"]
        }

        d = Database("admin")
        ret = parse(d, test["text"])
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]

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
        
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]


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
        
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]
            assert ret[-1]["output"] == test["output"]

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
        
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]
            for k in ret[-1]["output"]:
                assert k in test["output"]
                assert ret[-1]["output"][k] == test["output"][k] 

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
        
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]
            assert ret[-1]["output"] == test["output"]


class Test_Append_Parse:

    def test_append_list(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset y =[]\nset z={first= "elem", second= "elem"}\nappend to x with "str"\n append to y with z\n append to y with z\nappend to x with y\nreturn x\n***'

        test = {
                "text": text1,
                "exp_status": ["SET", "SET", "SET", "APPEND", "APPEND", "APPEND", "APPEND", "RETURNING"],
                "output": ["str", {"first": "elem", "second": "elem"}, {"first": "elem", "second": "elem"}]
        }

        d = Database("admin")
        ret = parse(d, test["text"])
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]
        for first, second in zip(test["output"], ret[-1]["output"]):
            if isinstance(first, dict):
                for k in first:
                    assert k in second
                    assert first[k] == second[k]
            else:
                assert first == second

    def test_append_str(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset z="str"\nappend to x with z\n append to x with z\nreturn x\n***'

        test = {
                "text": text1,
                "exp_status": ["SET", "SET", "APPEND", "APPEND", "RETURNING"],
                "output": ["str", "str"]
        }

        d = Database("admin")
        ret = parse(d, test["text"])
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]
        for first, second in zip(test["output"], ret[-1]["output"]):
            assert first == second

    def test_append_dict(self):
        text1 = 'as principal admin password "admin" do\nset x=[]\nset z={first="elem", second="elem"}\nappend to x with z\n append to x with z\nreturn x\n***'

        test = {
                "text": text1,
                "exp_status": ["SET", "SET", "APPEND", "APPEND", "RETURNING"],
                "output": [{"first": "elem", "second": "elem"}, {"first": "elem", "second": "elem"}]
        }

        d = Database("admin")
        ret = parse(d, test["text"])
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]
        for first, second in zip(test["output"], ret[-1]["output"]):
            for k in first:
                assert k in second
                assert first[k] == second[k]

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
        for test in tests:
            ret = parse(d, test["text"])
            assert len(ret) == len(test["exp_status"])
            for i, code in enumerate(ret):
                assert code["status"] == test["exp_status"][i]