import { ADMIN, ALL, APPEND, DELEGATE, DELEGATION, READ, SET, SET_DELEGATION_STATUS, WRITE } from '../constants';
// prettier-ignore
import { addToStatuses, delegateData, getCurrentPrincipal, getWorkingPrincipals, getWorkingVariables, hasPermissionTo, markHadFailure, markHadSecurityViolation } from '../data';

// set delegation <tgt> q <right> -> p

// example: set delegation messageVar admin read -> alice

// When <tgt> is a variable x, Indicates that q delegates <right> to p on x, so that p is given <right> whenever q is.
// If p is anyone, then effectively all principals are given <right> on x (for more detail, see here).
// When <tgt> is the keyword 'all' then q delegates <right> to p for all variables on which q (currently) has delegate permission.

// Failure conditions:

// Fails if either p or q does not exist
// Fails if x does not exist or if it is a local variable, if <tgt> is a variable x.
// Security violation unless the current principal is admin or q;
// if the principal is q and <tgt> is the variable x, then q must have delegate permission on x.
// Successful status code: SET_DELEGATION

export const setDelegationCommand = (command: string) => {
    // console.log(`Running 'set delegation' command: '${command}'...`);

    command = command.slice(command.indexOf(SET) + SET.length).trim(); // gets rid of set keyword
    command = command.slice(command.indexOf(DELEGATION) + DELEGATION.length).trim(); // gets rid of delegation keyword, puts expression at front

    const nameOfTarget = command.substring(0, command.indexOf(' ')).trim();

    command = command.slice(command.indexOf(' ')).trim(); // get rid of target

    const giverPrincipal = command.substring(0, command.indexOf(' ')).trim();

    command = command.slice(command.indexOf(' ')).trim(); // get rid of giver principal

    const rightToGive = command.substring(0, command.indexOf(' ')).trim();

    command = command.slice(command.indexOf(' ')).trim(); // get rid of right
    command = command.slice(command.indexOf('->') + '->'.length).trim(); // get rid of arrow

    const takerPrincipal = command.substring(command.indexOf(' ')).trim();

    // does q (giver principal) exist?
    if (!getWorkingPrincipals()[`${giverPrincipal}`]) {
        markHadFailure();
        return;
    }

    // is current principal not q (giver principal) or not admin? (security violation)
    if (getCurrentPrincipal() !== giverPrincipal && getCurrentPrincipal() !== ADMIN) {
        markHadSecurityViolation();
        return;
    }

    // does p (getter principal) exist?
    if (!getWorkingPrincipals()[`${takerPrincipal}`]) {
        markHadFailure();
        return;
    }

    // does target (varname) exist? (if not 'all')
    if (!getWorkingVariables()[`${nameOfTarget}`] && nameOfTarget !== ALL) {
        markHadFailure();
        return;
    }

    // is target a local? (if not 'all')
    if (getWorkingVariables()[`${nameOfTarget}`].isLocal && nameOfTarget !== ALL) {
        markHadFailure();
        return;
    }

    if (![READ, WRITE, DELEGATE, APPEND].includes(rightToGive)) {
        markHadFailure();
        return;
    }

    if (nameOfTarget === ALL) {
        // When <tgt> is the keyword all then q delegates <right> to p for all variables on which q (currently) has delegate permission.
        for (const varname of Object.keys(getWorkingVariables())) {
            if (hasPermissionTo(varname, giverPrincipal, 'delegate') || giverPrincipal === ADMIN) {
                switch (rightToGive) {
                    case READ:
                        delegateData(varname, takerPrincipal, giverPrincipal, 'read');
                        break;
                    case WRITE:
                        delegateData(varname, takerPrincipal, giverPrincipal, 'write');
                        break;
                    case APPEND:
                        delegateData(varname, takerPrincipal, giverPrincipal, 'append');
                        break;
                    case DELEGATE:
                        delegateData(varname, takerPrincipal, giverPrincipal, 'delegate');
                        break;
                    default:
                        markHadFailure();
                        return;
                }
            }
        }
    } else {
        // specific variable to set delegation
        // if the principal is q and <tgt> is the variable x, then q must have delegate permission on x.
        if (!hasPermissionTo(nameOfTarget, giverPrincipal, 'delegate') && getCurrentPrincipal() !== ADMIN) {
            markHadSecurityViolation();
            return;
        }

        switch (rightToGive) {
            case READ:
                delegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'read');
                break;
            case WRITE:
                delegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'write');
                break;
            case APPEND:
                delegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'append');
                break;
            case DELEGATE:
                delegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'delegate');
                break;
            default:
                markHadFailure();
                return;
        }
    }

    addToStatuses({
        status: SET_DELEGATION_STATUS
    });
};
