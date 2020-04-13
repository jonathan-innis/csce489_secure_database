from lark import Lark, Tree, Transformer, Token
import sys
from commands import *

class ProgramParser():
    grammar = r'''
        start       : _ASPRINCIPAL IDENTIFIER "password" STRING "do" _ENDLINE _cmd* progend END -> asprincipal

        progend     : "exit" _ENDLINE -> exit
                    | "return" expr _ENDLINE -> returnval

        _cmd        : primcmd _ENDLINE
                    | _ENDLINE

        expr        : _value -> value
                    | EMPTYARRAY -> array
                    | "{" _fieldvals "}" -> record

        _fieldvals  : IDENTIFIER "=" _value
                    | IDENTIFIER "=" _value "," _fieldvals

        _value      : IDDOTID
                    | IDENTIFIER
                    | STRING

        primcmd     : "create" "principal" IDENTIFIER STRING -> createprincipal
                    | "change" "password" IDENTIFIER STRING -> changepassword
                    | "set" IDENTIFIER "=" expr -> setidentifier
                    | "append" "to" IDENTIFIER "with" expr -> appendto
                    | "local" IDENTIFIER "=" expr -> localidentifier
                    | "foreach" IDENTIFIER "in" IDENTIFIER "replacewith" expr -> foreachidentifier
                    | "set" "delegation" _tgt IDENTIFIER right "->" IDENTIFIER -> setdelegation
                    | "delete" "delegation" _tgt IDENTIFIER right "->" IDENTIFIER -> deletedelegation
                    | "default" "delegator" "=" IDENTIFIER -> defaultdelegator

        _tgt        : ALL
                    | IDENTIFIER

        right       : "read" -> read
                    | "write" -> write
                    | "append" -> append
                    | "delegate" -> delegate

        END         : /\*\*\*$/
        _ENDLINE    : /([\/][\/][A-Za-z0-9_ ,;\.?!-]*)?\n/
        STRING      : /"[A-Za-z0-9_ ,;\.?!-]*"/
        IDENTIFIER  : /[A-Za-z][A-Za-z0-9_]*/
        IDDOTID     : /[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*/

        EMPTYARRAY  : "[]"

        _ASPRINCIPAL: /as[ ]+principal/
        ALL         : "all"
        %ignore " "
        '''
    def __init__(self):
        self.larkParser = Lark(ProgramParser.grammar)
        
    def parseProgram(self, program):
        if (len(program) > 1000000):
            raise ProgramSizeException("Program size must not exceed 1,000,000 characters")
        tree = self.larkParser.parse(program)
        collectCommands = CollectCommands()
        collectCommands.transform(tree)
        return collectCommands.commands

keywords = {"all", "append", "as", "change", "create", "default", "delegate",
        "delegation", "delegator", "delete", "do", "exit", "foreach", "in",
        "local", "password", "principal", "read", "replacewith", "return",
        "set", "to", "write", "***"}

def checkForKeyWord(identifier):
    if (identifier in keywords):
        raise KeywordInIdentifierException("Exception: Keyword used as an identifier")
    return identifier

def tryAddKeyValue(recordDict, key, value):
    if (recordDict.get(key) != None):
        pass
        raise DuplicateKeyException("Exception: Duplicate keys in Record literal")
    recordDict[key] = value

def evalExpression(tree):
    if (tree.data == 'value'):
        return tree.children[0].value
    if (tree.data == 'array'):
        return NewArray()
    if (tree.data == 'record'):
        fieldVals = {}
        for i in range(0, len(tree.children)//2):
            identifier = tree.children[i*2].value
            value = tree.children[i*2 +1].value
            tryAddKeyValue(fieldVals, identifier.value, RecordItem(value))
        return Record(fieldVals)

class CollectCommands(Transformer):
    def __init__(self):
        self.commands = []

    def ALL(self, item):
        item.value = AllTarget()
        return item

    def IDENTIFIER(self, item):
        if (len(item.value) > 255):
            raise ValueError('Identifier length greater than 255')
        item.value = Identifier(checkForKeyWord(item.value))
        return item

    def IDDOTID(self, item):
        identifiers = item.value.split('.')
        for identifier in identifiers:
            if (len(identifier) > 255):
                raise ValueError('Identifier length greater than 255')
            checkForKeyWord(identifier)
        item.value = RecordIdentifier(item.value)
        return item

    def STRING(self, item):
        item.value = item.value.strip('\"')
        if (len(item.value) > 65535):
            raise ValueError('Identifier length greater than 255')
        item.value = Value(item.value)
        return item

    def createprincipal(self, items):
        self.commands.append(CreatePrincipal(items[0].value, items[1].value))
    
    def changepassword(self, items):
        self.commands.append(ChangePassword(items[0].value, items[1].value))

    def setidentifier(self, items):
        identifier = items[0].value
        expr = evalExpression(items[1])
        self.commands.append(Set(identifier, expr))
            
    def appendto(self, items):
        identifier = items[0].value
        expr = evalExpression(items[1])
        self.commands.append(AppendTo(identifier, expr))

    def localidentifier(self, items):
        identifier = items[0].value
        expr = evalExpression(items[1])
        self.commands.append(Local(identifier, expr))

    def foreachidentifier(self, items):
        itemIdentifier = items[0].value
        containerIdentifier = items[1].value
        expr = evalExpression(items[2])
        if (isinstance(expr, NewArray)):
            raise ArrayInForeachException("Exception: Foreach Statement expression evaluated to NewArray")
        incompleteKeys = set()
        if type(expr) is Record:
            for key, value in expr.items.items():
                if isinstance(value.value, Identifier) and value.value.value == itemIdentifier.value:
                    incompleteKeys.add(key)
                    # expr.items[key] = ForEachIterVar(value.value)
        
        if incompleteKeys:
            for key in incompleteKeys:
                del expr.items[key]
            expr = IncompleteRecord(Record(expr.items), incompleteKeys)
    
        self.commands.append(Foreach(itemIdentifier, containerIdentifier, expr))

    def setdelegation(self, items):
        target = items[0].value
        authorizerIdentifier = items[1].value
        right = items[2].data
        delegateeIdentifier = items[3].value
        self.commands.append(SetDelegation(target, authorizerIdentifier, right, delegateeIdentifier))
    
    def deletedelegation(self, items):
        target = items[0].value
        authorizerIdentifier = items[1].value
        right = items[2].data
        delegateeIdentifier = items[3].value
        self.commands.append(DeleteDelegation(target, authorizerIdentifier, right, delegateeIdentifier))

    def defaultdelegator(self, items):
        self.commands.append(DefaultDelegator(items[0].value))
    
    def returnval(self, items):
        expr = evalExpression(items[0])
        self.commands.append(ReturnValue(expr))
    
    def exit(self, items):
        self.commands.append(Exit())
    
    def asprincipal(self, items):
        principalIdentifier = items[0].value
        principalPassword = items[1].value
        self.commands.insert(0, Login(principalIdentifier, principalPassword))


def main():
    f = open(sys.argv[1], "r")
    contents = f.read()
    f.close()
    parser = ProgramParser()
    commands = parser.parseProgram(contents.rstrip())
    print(commands[0])
    for command in commands[1:]:
        print('        ' + str(command))
    print('***')
    return commands

if __name__ == "__main__":
    main()
