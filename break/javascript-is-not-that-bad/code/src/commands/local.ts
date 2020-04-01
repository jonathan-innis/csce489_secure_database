import { ADMIN, IDENTIFIEREXPRESSION, LOCAL, LOCAL_STATUS, RESERVED_WORDS } from '../constants';
// prettier-ignore
import { addToStatuses, addVariable, delegateData, getCurrentPrincipal, getWorkingVariables, markHadFailure, setLocal, setVariableValue } from '../data';
import { evalExpression } from './expression';

// local x = <expr>

// Creates a local variable x and initializes it to the value of executing <expr>.
// Subsequent updates to x can be made as you would to a global variable,
// e.g., using set x, append...to x, foreach, etc. as described elsewhere in this section.
// Different from a global variable, local variables are destroyed when the program ends—they do not persist across connections.

// Failure conditions:

// Fails if x is already defined as a local or global variable.
// May fail or have a security violation due to evaluating <expr>
// Successful status code: LOCAL

export const localCommand = (command: string) => {
    // console.log(`Running 'local' command: '${command}'...`);

    command = command.slice(command.indexOf(LOCAL) + LOCAL.length).trim(); // gets rid of local keyword

    const nameOfVar = command.substring(0, command.indexOf(' ')).trim();

    if (nameOfVar.length > 255) {
        markHadFailure();
        return;
    }

    if (!IDENTIFIEREXPRESSION.test(nameOfVar)) {
        markHadFailure();
        return;
    }

    if (RESERVED_WORDS.includes(nameOfVar)) {
        markHadFailure();
        return;
    }

    command = command.slice(command.indexOf(' ')).trim(); // '=' is at the front
    const expression = command.slice(command.indexOf('=') + '='.length).trim(); // get rid of '='

    // Don't use LOCAL to re-set variables, fail if already exists
    if (getWorkingVariables()[`${nameOfVar}`]) {
        markHadFailure();
        return;
    }

    const currentPrincipal = getCurrentPrincipal();

    // we already checked that it didn't exist, adding it
    addVariable(nameOfVar, 'TEMPORARY_STRING_VALUE', 'string');
    setLocal(nameOfVar);
    if (currentPrincipal !== ADMIN) {
        delegateData(nameOfVar, currentPrincipal, ADMIN, 'read');
        delegateData(nameOfVar, currentPrincipal, ADMIN, 'write');
        delegateData(nameOfVar, currentPrincipal, ADMIN, 'append');
        delegateData(nameOfVar, currentPrincipal, ADMIN, 'delegate');
    }

    const evaluatedExpression = evalExpression(expression, null, null);
    if (!evaluatedExpression) {
        return;
    }

    setVariableValue(nameOfVar, evaluatedExpression.value, evaluatedExpression.varType);
    addToStatuses({
        status: LOCAL_STATUS
    });
};
