// default delegator = p

import { DEFAULT, DELEGATOR, ADMIN, DEFAULT_DELEGATOR } from '../constants';
import { getWorkingPrincipals, markHadFailure, getCurrentPrincipal, markHadSecurityViolation, updateDefaultDelegator, addToStatuses } from '../data';

// Sets the “default delegator” to p.
// This means that when a principal q is created, the system automatically delegates all from p to q.
// Changing the default delegator does not affect the permissions of existing principals.
// The initial default delegator is anyone.

// Failure conditions:

// Fails if p does not exist
// Security violation if the current principal is not admin.
// Successful status code: DEFAULT_DELEGATOR

export const defaultDelegatorCommand = (command: string) => {
    command = command.slice(command.indexOf(DEFAULT) + DEFAULT.length).trim(); // gets rid of default keyword
    command = command.slice(command.indexOf(DELEGATOR) + DELEGATOR.length).trim(); // gets rid of delegator keyword, puts expression at front
    const newDefaultDelegator = command.slice(command.indexOf('=') + '='.length).trim(); // gets rid of = keyword, puts expression at front

    if (!getWorkingPrincipals()[`${newDefaultDelegator}`]) {
        markHadFailure();
        return;
    }

    if (getCurrentPrincipal() !== ADMIN) {
        markHadSecurityViolation();
        return;
    }

    updateDefaultDelegator(newDefaultDelegator);

    addToStatuses({
        status: DEFAULT_DELEGATOR
    });
};
