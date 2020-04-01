import { RETURN, RETURNING_STATUS } from '../constants';
import { addToStatuses } from '../data';
import { evalExpression } from './expression';

// If the command is return <expr> then the server executes the expression and outputs status code
// RETURNING and the JSON representation of the result for the key "output"; the output format is
// given at the end of this document.

export const returnCommand = (command: string) => {
    command = command.slice(command.indexOf(RETURN) + RETURN.length).trim(); // gets rid of return keyword, puts expression at front

    const evaluatedExpression = evalExpression(command, null, null);
    if (!evaluatedExpression) {
        return;
    }

    addToStatuses({
        status: RETURNING_STATUS,
        output: evaluatedExpression.value
    });
};
