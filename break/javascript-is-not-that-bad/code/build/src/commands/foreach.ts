// foreach y in x replacewith <expr>

import { ADMIN, FOREACH, FOREACH_STATUS, IDENTIFIEREXPRESSION, IN, REPLACEWITH } from '../constants';
import {
    addToStatuses,
    getCurrentPrincipal,
    getWorkingVariables,
    hasPermissionTo,
    markHadFailure,
    markHadSecurityViolation,
    setVariableValue
} from '../data';
import { evalExpression } from './expression';

// For each element y in list x, replace the contents of y with the result of executing <expr>.
// This expression is called for each element in x, in order, and y is bound to the current element.

// As an example, consider the following program:

// as principal admin password "admin" do
//    set records = []
//    append to records with { name = "mike", date = "1-1-90" }
//    append to records with { name = "dave", date = "1-1-85" }
//    local names = records
//    foreach rec in names replacewith rec.name
//    return names
// ***

// This program creates a list of two records, each with fields name and date.
// Then it makes a copy of this list in names, and updates the contents of names using foreach.
// This foreach iterates over the list and replaces each record with the first element of that record.
// So the final, returned variable names is ["mike","dave"].
// (The original list records is not changed by the foreach here.)

// Failure conditions:

// -Fails if x is not defined
// -Security violation if the current principal does not have read and write permission on x.
// -Fails if y is already defined as a local or global variable.
// -Fails if x is not a list.
// If any execution of <expr> fails or has a security violation, then entire foreach does. <expr> is from the front of the list to the back
// Fails if <expr> evaluates to a list, rather than a string or a record.
// Successful status code: FOREACH

// foreach y in x replacewith <expr>

export const foreachCommand = (command: string) => {
    command = command.slice(command.indexOf(FOREACH) + FOREACH.length).trim(); // get rid of 'foreach' word

    const y = command.substring(0, command.indexOf(' ')).trim();

    if (y.length > 255) {
        markHadFailure();
        return;
    }

    if (!IDENTIFIEREXPRESSION.test(y)) {
        markHadFailure();
        return;
    }

    command = command.slice(command.indexOf(' ')).trim(); // 'in' is at the front
    command = command.slice(command.indexOf(IN) + IN.length).trim(); // get rid of 'in'

    const x = command.substring(0, command.indexOf(' ')).trim();

    command = command.slice(command.indexOf(' ')).trim(); // 'replacewith' is at the front
    const expression = command.slice(command.indexOf(REPLACEWITH) + REPLACEWITH.length).trim(); // get rid of 'replacewith'

    // fails if x not defined
    if (!getWorkingVariables()[`${x}`]) {
        markHadFailure();
        return;
    }

    // security if -> must have read and write on x
    if (
        (!hasPermissionTo(x, getCurrentPrincipal(), 'read') || !hasPermissionTo(x, getCurrentPrincipal(), 'write')) &&
        getCurrentPrincipal() !== ADMIN
    ) {
        markHadSecurityViolation();
        return;
    }

    // fails if y already defined as local or global
    if (getWorkingVariables()[`${y}`]) {
        markHadFailure();
        return;
    }

    // fails if x is not a list
    if (getWorkingVariables()[`${x}`].varType !== 'list') {
        markHadFailure();
        return;
    }

    const listObject: any[] = getWorkingVariables()[`${x}`].value;

    for (let listIndex = 0; listIndex < listObject.length; listIndex++) {
        if (expression[0] === '"' || expression[0] === '{' || !expression.includes('.')) {
            const expressionThing = evalExpression(expression, y, listObject[listIndex]);
            if (!expressionThing || expressionThing.varType === 'list') {
                markHadFailure();
                return;
            }
            listObject[listIndex] = expressionThing.value;
            continue;
        }

        // foreach y in x replacewith ?.?
        // what is the first half?
        const firstPart = expression.substring(0, expression.indexOf('.')).trim();
        // some regular expression
        if (firstPart !== y) {
            const expressionThing = evalExpression(expression, null, null);
            if (!expressionThing || expressionThing.varType === 'list') {
                markHadFailure();
                return;
            }
            listObject[listIndex] = expressionThing.value;
            continue;
        }

        // first half is representing the current item in the list, and we are thinking it's a record
        // what is the second half?
        const secondPart = expression.substring(expression.indexOf('.') + '.'.length, expression.length);
        try {
            listObject[listIndex] = listObject[listIndex][`${secondPart}`];
        } catch (error) {
            markHadFailure();
            return;
        }
    }

    setVariableValue(x, listObject, 'list');

    addToStatuses({
        status: FOREACH_STATUS
    });
};
