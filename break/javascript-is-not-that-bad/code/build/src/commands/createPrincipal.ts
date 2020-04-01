import { ADMIN, CREATE, CREATE_PRINCIPAL_STATUS, IDENTIFIEREXPRESSION, PRINCIPAL, RESERVED_WORDS, STRINGEXPRESSION_NOQUOTES } from '../constants';
// prettier-ignore
import { addToStatuses, createPrincipalData, delegateData, getCurrentPrincipal, getDefaultDelegator, getWorkingPrincipals, getWorkingVariables, hasPermissionTo, markHadFailure, markHadSecurityViolation } from '../data';

// create principal p s

// Creates a principal p having password s.

// The system is preconfigured with principal admin whose password is given by the second command-line argument; or "admin" if that password is not given. There is also a preconfigured principal anyone whose initial password is unspecified, and which has no inherent authority. (See also the description of default delegator, below, for more about this command, and see the permissions discussion for more on how principal anyone is used.)

// Failure conditions:

// Fails if p already exists as a principal.
// Security violation if the current principal is not admin.
// Successful status code: CREATE_PRINCIPAL

export const createPrincipalCommand = (command: string) => {
    // console.log(`Running 'create principal' command: '${command}'...`);

    // is the current principal an admin?
    if (getCurrentPrincipal() !== ADMIN) {
        markHadSecurityViolation();
        return;
    }

    command = command.slice(command.indexOf(CREATE) + CREATE.length).trim(); // get rid of leading word 'create'
    command = command.slice(command.indexOf(PRINCIPAL) + PRINCIPAL.length).trim(); // get rid of leading word 'principal'

    // next word is name
    const name = command.substring(0, command.indexOf(' ')).trim(); // shouldn't need trim....(excessive use of it might be confusing....)
    command = command.slice(command.indexOf(' ')).trim();

    if (name.length > 255) {
        markHadFailure();
        return;
    }

    if (!IDENTIFIEREXPRESSION.test(name)) {
        markHadFailure();
        return;
    }

    if (RESERVED_WORDS.includes(name)) {
        markHadFailure();
        return;
    }

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

    // Principal already exists
    if (getWorkingPrincipals()[`${name}`]) {
        markHadFailure();
        return;
    }

    createPrincipalData(name, password);

    const giverPrincipal = getDefaultDelegator();

    for (const varname of Object.keys(getWorkingVariables())) {
        if (hasPermissionTo(varname, giverPrincipal, 'delegate') || giverPrincipal === ADMIN) {
            delegateData(varname, name, giverPrincipal, 'read');
            delegateData(varname, name, giverPrincipal, 'write');
            delegateData(varname, name, giverPrincipal, 'append');
            delegateData(varname, name, giverPrincipal, 'delegate');
        }
    }

    addToStatuses({
        status: CREATE_PRINCIPAL_STATUS
    });
};
