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