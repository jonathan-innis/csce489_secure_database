import { ADMIN, APPEND, APPEND_STATUS, TO, WITH } from '../constants';
// prettier-ignore
import { addToStatuses, getCurrentPrincipal, getWorkingVariables, hasPermissionTo, markHadFailure, markHadSecurityViolation, setVariableValue } from '../data';
import { evalExpression } from './expression';

// append to x with <expr>

// Adds the <expr>’s result to the end of x.
// If <expr> evaluates to a record or a string, it is added to the end of x;
// if <expr> evaluates to a list, then it is concatenated to (the end of) x.

// Failure conditions:

// Fails if x is not defined
// Security violation if the current principal does not have either write or append permission on x (read permission is not necessary).
// Fails if x is not a list
// May fail or have a security violation due to evaluating <expr>
// Successful status code: APPEND

export const appendToCommand = (command: string) => {
    // console.log(`Running 'append to' command: '${command}'...`);
    command = command.slice(command.indexOf(APPEND) + APPEND.length).trim(); // get rid of leading word 'append'
    command = command.slice(command.indexOf(TO) + TO.length).trim(); // get rid of leading word 'to'

    // next word is varname
    const nameOfVar = command.substring(0, command.indexOf(' ')).trim();

    command = command.slice(command.indexOf(' ')).trim(); // 'with' is at the front
    const expression = command.slice(command.indexOf(WITH) + WITH.length).trim(); // get rid of 'with'

    // fails if var doesn't exist
    if (!getWorkingVariables()[`${nameOfVar}`]) {
        markHadFailure();
        return;
    }

    // fails if x is not a list
    if (getWorkingVariables()[`${nameOfVar}`].varType !== 'list') {
        markHadFailure();
        return;
    }

    const currentPrincipal = getCurrentPrincipal();

    // security violation if current principal does not have either write or append permission (read not required)
    if (
        !(hasPermissionTo(nameOfVar, currentPrincipal, 'write') || hasPermissionTo(nameOfVar, currentPrincipal, 'append')) &&
        currentPrincipal !== ADMIN
    ) {
        markHadSecurityViolation();
        return;
    }

    // append to x with "string"
    // append to x with y.z
    // append to x with y
    // append to x with [] -> do nothing?
    // append to x with { field = "string", field2 = x.y, field3 = x}

    const wholeExpression = evalExpression(expression, null, null);
    if (!wholeExpression) {
        return;
    }

    const { value } = getWorkingVariables()[`${nameOfVar}`];

    const valueOfExpression = wholeExpression.value;
    const typeOfExpression = wholeExpression.varType;

    if (typeOfExpression === 'list') {
        // setVariableValue(nameOfVar, [...value, ...wholeExpression.value], 'list');
        setVariableValue(nameOfVar, (value as any[]).concat(wholeExpression.value), 'list');
    } else {
        (value as any[]).push(valueOfExpression);
        setVariableValue(nameOfVar, value, 'list');
    }

    // setVariableValue(nameOfVar, [...value, ...wholeExpression.value], 'list');

    addToStatuses({
        status: APPEND_STATUS
    });
};
