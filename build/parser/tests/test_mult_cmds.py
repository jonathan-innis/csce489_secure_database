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
        d.reset(rollback=False)


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