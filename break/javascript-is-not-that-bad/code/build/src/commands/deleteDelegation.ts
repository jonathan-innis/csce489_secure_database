import { ADMIN, ALL, APPEND, DELEGATE, DELEGATION, DELETE, DELETE_DELEGATION, READ, WRITE } from '../constants';
// prettier-ignore
import { addToStatuses, getCurrentPrincipal, getWorkingPrincipals, getWorkingVariables, hasPermissionTo, markHadFailure, markHadSecurityViolation, undelegateData } from '../data';

// delete delegation <tgt> q <right> -> p

// When <tgt> is a variable x, indicates that q revokes a delegation assertion of <right> to p on x.
// In effect, this command revokes a previous command set delegation x q <right> -> p;
// see below for the precise semantics of what this means.
// If <tgt> is the keyword all then q revokes delegation of <right> to p for all variables on which q has delegate permission.

// Failure conditions:

// Fails if either p or q does not exist
// Fails if x does not exist or if it is a local variable, if <tgt> is a variable x.
// Security violation unless the current principal is admin, p, or q;
// if the principal is q and <tgt> is a variable x, then it must have delegate permission on x.
// (No special permission is needed if the current principal is p: any non-admin principal can always deny himself rights).
// Successful status code: DELETE_DELEGATION

export const deleteDelegationCommand = (command: string) => {
    // console.log(`Running 'delete delegation' command: '${command}'...`);

    command = command.slice(command.indexOf(DELETE) + DELETE.length).trim(); // gets rid of set keyword
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

    // does p (taker principal) exist?
    if (!getWorkingPrincipals()[`${takerPrincipal}`]) {
        markHadFailure();
        return;
    }

    // is current principal not q (giver principal) or not admin? (security violation)
    if (getCurrentPrincipal() !== giverPrincipal && getCurrentPrincipal() !== ADMIN && getCurrentPrincipal() !== takerPrincipal) {
        markHadSecurityViolation();
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
                        undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'read');
                        break;
                    case WRITE:
                        undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'write');
                        break;
                    case APPEND:
                        undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'append');
                        break;
                    case DELEGATE:
                        undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'delegate');
                        break;
                    default:
                        markHadFailure();
                        return;
                }
            }
        }
    } else {
        // specific variable to set delegation
        // if the principal is q and <tgt> is the variable x, then q must have delegate permission on x. (but could deny themselves rights)
        if (!hasPermissionTo(nameOfTarget, giverPrincipal, 'delegate') && getCurrentPrincipal() !== ADMIN && giverPrincipal !== takerPrincipal) {
            markHadSecurityViolation();
            return;
        }

        switch (rightToGive) {
            case READ:
                undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'read');
                break;
            case WRITE:
                undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'write');
                break;
            case APPEND:
                undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'append');
                break;
            case DELEGATE:
                undelegateData(nameOfTarget, takerPrincipal, giverPrincipal, 'delegate');
                break;
            default:
                markHadFailure();
                return;
        }
    }

    addToStatuses({
        status: DELETE_DELEGATION
    });
};
