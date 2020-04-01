import { ADMIN, CHANGE, CHANGE_PASSWORD_STATUS, PASSWORD, STRINGEXPRESSION_NOQUOTES } from '../constants';
import { addToStatuses, changePasswordData, getCurrentPrincipal, getWorkingPrincipals, markHadFailure, markHadSecurityViolation } from '../data';

// change password p s

// Changes the principal p’s password to s.

// Failure conditions:

// Fails if p does not exist
// Security violation if the current principal is neither admin nor p itself.
// Successful status code: CHANGE_PASSWORD

export const changePasswordCommand = (command: string) => {
    // console.log(`Running 'change password' command: '${command}'...`);

    command = command.slice(command.indexOf(CHANGE) + CHANGE.length).trim(); // get rid of leading word 'change'
    command = command.slice(command.indexOf(PASSWORD) + PASSWORD.length).trim(); // get rid of leading word 'password'

    // next word is name
    const name = command.substring(0, command.indexOf(' ')).trim(); // shouldn't need trim....(excessive use of it might be confusing....)
    command = command.slice(command.indexOf(' ')).trim();

    // rest of command is password in quotes (should be)
    const password = command.substring(1, command.length - 1);

    if (password.length > 65535) {
        markHadFailure();
        return;
    }

    if (!STRINGEXPRESSION_NOQUOTES.test(password)) {
        markHadFailure();
        return;
    }

    // Did not find principal, does not exist in data
    if (!getWorkingPrincipals()[`${name}`]) {
        markHadFailure();
        return;
    }

    // must be admin or this principal
    if (getCurrentPrincipal() !== ADMIN && name !== getCurrentPrincipal()) {
        markHadSecurityViolation();
        return;
    }

    changePasswordData(name, password);

    addToStatuses({
        status: CHANGE_PASSWORD_STATUS
    });
};
