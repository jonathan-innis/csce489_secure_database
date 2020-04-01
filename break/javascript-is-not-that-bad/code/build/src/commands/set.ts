import { ADMIN, IDENTIFIEREXPRESSION, RESERVED_WORDS, SET, SET_STATUS } from '../constants';
// prettier-ignore
import { addToStatuses, addVariable, delegateData, getCurrentPrincipal, getWorkingVariables, hasPermissionTo, markHadFailure, markHadSecurityViolation, setVariableValue } from '../data';
import { evalExpression } from './expression';

// set x = <expr>

// Sets x’s value to the result of evaluating <expr>, where x is a global or local variable.
// If x does not exist this command creates it as a global.
// If x is created by this command, and the current principal is not admin,
// then the current principal is delegated read, write, append, and delegate rights from the
// admin on x (equivalent to executing set delegation x admin read -> p and
// set delegation x admin write -> p, etc. where p is the current principal).

// Setting a variable results in a “deep copy.”  For example, consider the following program:

// set x = "hello"
// set y = x
// set x = "there"

// At this point, y is still "hello" even though we have re-set x.

// Failure conditions:

// May fail or have a security violation due to evaluating <expr>
// Security violation if the current principal does not have write permission on x.
// Successful status code: SET

export const setCommand = (command: string) => {
    command = command.slice(command.indexOf(SET) + SET.length).trim(); // gets rid of set keyword, puts expression at front

    const nameOfVar = command.substring(0, command.indexOf(' ')).trim();

    if (nameOfVar.length > 255) {
        markHadFailure();
        return;
    }

    if (!IDENTIFIEREXPRESSION.test(nameOfVar)) {
        // console.log(`var that failed was '${nameOfVar}' against ${IDENTIFIEREXPRESSION}`);

        markHadFailure();
        return;
    }

    if (RESERVED_WORDS.includes(nameOfVar)) {
        markHadFailure();
        return;
    }

    // console.log(`var that passed was '${nameOfVar}' against ${IDENTIFIEREXPRESSION}`);

    command = command.slice(command.indexOf(' ')).trim(); // '=' is at the front
    const expression = command.slice(command.indexOf('=') + 1).trim(); // get rid of '='

    const currentPrincipal = getCurrentPrincipal();

    if (!getWorkingVariables()[`${nameOfVar}`]) {
        // create the var, just put random stuff for values for now, will change later
        addVariable(nameOfVar, 'TEMPORARY_STRING_VALUE', 'string');

        if (currentPrincipal !== ADMIN) {
            delegateData(nameOfVar, currentPrincipal, ADMIN, 'read');
            delegateData(nameOfVar, currentPrincipal, ADMIN, 'write');
            delegateData(nameOfVar, currentPrincipal, ADMIN, 'append');
            delegateData(nameOfVar, currentPrincipal, ADMIN, 'delegate');
        }
    }

    // console.log('got to set');

    // variable should now exist (assumed)
    if (!hasPermissionTo(nameOfVar, currentPrincipal, 'write') && currentPrincipal !== ADMIN) {
        markHadSecurityViolation();
        return;
    }

    const evaluatedExpression = evalExpression(expression, null, null);
    if (!evaluatedExpression) {
        return;
    }

    setVariableValue(nameOfVar, evaluatedExpression.value, evaluatedExpression.varType);
    addToStatuses({
        status: SET_STATUS
    });
};
