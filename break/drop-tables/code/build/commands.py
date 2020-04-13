class DuplicateKeyException(Exception):
    pass

class ArrayInForeachException(Exception):
    pass

class KeywordInIdentifierException(Exception):
    pass

class ProgramSizeException(Exception):
    pass

class AllTarget():
    def __init__(self):
        pass
    def __str__(self):
        return 'all'

class NewArray():
    """ a class to represent an expression that evaluated to an empty array, or
    [].
    """
    def __init__(self):
        pass
    def __str__(self):
        return '[]'

class Value():
    """ A class to represent an expression that evaulated to a string literal.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return '"' + self.value + '"'

class Identifier():
    """ A class to represent an expression that evaulated to an identfier, such
    as X, variableName, recordVar.recordItem .
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class ForEachIterVar(Identifier):
    def __init__(self, value):
        super().__init__(value)

    def __str__(self):
        return super().__str__()

class RecordIdentifier():
    def __init__(self, value):
        values = value.split('.')
        self.recordName = values[0]
        self.recordKey = values[1]
    def __str__(self):
        return self.recordName + '.' + self.recordKey

class Record():
    def __init__(self, recordItemDict):
        self.items = recordItemDict
    def __str__(self):
        retVal = '{ ' + str(list(self.items.keys())[0]) + ' = ' + str(list(self.items.values())[0])
        for key, recordItem in self.items.items():
            retVal += ', ' + str(key) + ' = ' + str(recordItem)
        retVal += ' }'
        return retVal

class IncompleteRecord():
    def __init__(self, completeRecord, incompleteKeys):
        self.completeRecord = completeRecord
        self.incompleteKeys = incompleteKeys

    def __str__(self):
        return f'{str(self.completeRecord)}\n{self.incompleteKeys}'

class RecordItem():
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class CreatePrincipal():
    def __init__(self, identifier, password):
        self.identifier = identifier
        self.password = password
    
    def __str__(self):
        return 'create principal ' + str(self.identifier) + ' ' + str(self.password)

class ChangePassword():
    def __init__(self, identifier, password):
        self.identifier = identifier
        self.password = password

    def __str__(self):
        return 'change password ' + str(self.identifier) + ' ' + str(self.password)

class Set():
    def __init__(self, identifier, expr):
        self.identifier = identifier
        self.expr = expr 
    def __str__(self):
        return 'set ' + str(self.identifier) + ' = ' + str(self.expr)

class AppendTo():
    def __init__(self, identifier, expr):
        self.identifier = identifier
        self.expr = expr 
    def __str__(self):
        return 'append to ' + str(self.identifier) + 'with' + str(self.expr)

class Local():
    def __init__(self, identifier, expr):
        self.identifier = identifier
        self.expr = expr
    def __str__(self):
        return 'local ' + str(self.identifier) + ' = ' + str(self.expr)

class Foreach():
    def __init__(self, itemVarIdentifier, containerVarIdentifier, expr):
        self.itemVarIdentifier = itemVarIdentifier
        self.containerVarIdentifier = containerVarIdentifier
        if (isinstance(expr, NewArray)):
            raise ArrayInForeachException('Array used as replacewith value in foreach statement')
        self.expr = expr
    def __str__(self):
        return 'foreach ' + str(self.itemVarIdentifier) + ' in ' + str(self.containerVarIdentifier) + ' replacewith ' + str(self.expr)
    
# authID delegates a right to delegatee on tgt
class SetDelegation():
    def __init__(self, target, authorizerIdentifier, right, delegateeIdentifier):
        self.target = target
        self.authorizerIdentifier = authorizerIdentifier
        self.right = right
        self.delegateeIdentifier = delegateeIdentifier

    def __str__(self):
        return 'set delegation ' + str(self.target) + ' ' + str(self.authorizerIdentifier) + ' ' + str(self.right) + ' -> ' + str(self.delegateeIdentifier)

class DeleteDelegation():
    def __init__(self, targetIdentifier, authorizerIdentifier, right, delegateeIdentifier):
        self.target = targetIdentifier 
        self.authorizerIdentifier = authorizerIdentifier 
        self.right = right
        self.delegateeIdentifier = delegateeIdentifier 
    def __str__(self):
        return 'delete delegation ' + str(self.target) + ' ' + str(self.authorizerIdentifier) + ' ' + self.right + ' -> ' + str(self.delegateeIdentifier)

class DefaultDelegator():
    def __init__(self, defaultDelegatorIdentifier):
        self.defaultDelegatorIdentifier = defaultDelegatorIdentifier
    def __str__(self):
        return 'default delegator = ' + str(self.defaultDelegatorIdentifier)

class ReturnValue():
    def __init__(self, returnValue):
        self.returnValue = returnValue
    def __str__(self):
        return 'return ' + str(self.returnValue)

class Exit():
    def __init__(self):
        pass
    def __str__(self):
        return 'exit'

class Login():
    def __init__(self, principalIdentifier, principalPassword):
        self.identifier = principalIdentifier
        self.password = principalPassword
    def __str__(self):
        return 'as principal ' + str(self.identifier) + ' password ' + str(self.password) + ' do'
