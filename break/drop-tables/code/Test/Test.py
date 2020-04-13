import sys
import glob, json

sys.path.append('../build')
from lark.exceptions import UnexpectedCharacters
from Parser import ProgramParser
from DataServer import DataServer

ignore_paths = {
    './Tests-Predefined/testfunc1.json',
    './Tests-Predefined/testtimeout1.json',
    './Tests-Predefined/testfunc3.json',
    './Tests-Predefined/test8.json',
    './Tests-Predefined/testlet3.json',
    './Tests-Predefined/testlet2.json',
    './Tests-Predefined/test4.json',
    './Tests-Predefined/testlet1.json',
    './Tests-Predefined/testperf1.json',
    './Tests-Predefined/testfilter1.json',
    './Tests-Predefined/testfilter2.json',
    './Tests-Predefined/testfunc2.json',
    './Tests-Predefined/testperf4.json'
}

# ignore_paths = {
#     './Tests-Predefined/testperf6.json'
# }

test_file_paths = glob.glob('./Tests-Predefined/*.json')
# print(test_file_paths)

for test_file_path in test_file_paths:
    if test_file_path in ignore_paths:
        print(f'IGNORING {test_file_path}')
        continue

    test_json = None
    with open(test_file_path) as test_file:
        test_json = json.load(test_file)
    data_server = DataServer('admin')
    # print(f'********{test_file_path}*********')
    # print('*********************************')
    # print('*********************************')
    x = 0
    # data_server = None
    for program_and_output in test_json['programs']:
        
        # print(data_server)
        program = program_and_output['program']
        print(f'****test: {test_file_path.split("/")[-1]}:{x} ****')
        x += 1
        parser = ProgramParser()
        try:
            commands = parser.parseProgram(program.rstrip())
        except(UnexpectedCharacters):
            print('Unexpected characters')
            continue
        except(ValueError):
            print('ValueError')
            continue

        output = data_server.execute_commands(commands)
        expected = program_and_output['output']
        print('---------------OUTPUT----------------------')
        print(output[-1])
        print('---------------EXPECT----------------------')
        print(expected[-1])
        print(output == expected)
        if output != expected:
            print(f'ooFailed: {test_file_path}')

        # run the program
    del data_server