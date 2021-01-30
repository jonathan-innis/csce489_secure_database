from Parser import ProgramParser
import commands
import unittest

def buildProgram(commands):
    program = str(commands[0])
    for command in commands[1:]:
        # newline, eight spaces, command
        program += '\n        ' + str(command)
    program += '\n***'
    return program

class TestParser(unittest.TestCase):
    parser = ProgramParser()
    def test_Identifiers(self):
        inputStr = """as principal admin password "password" do
        create principal bob "otherpassword"
        local x = string
        exit
***"""
        self.assertEqual(inputStr, buildProgram(TestParser.parser.parseProgram(inputStr)))

if __name__ == '__main__':
    unittest.main()
