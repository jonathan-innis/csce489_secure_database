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