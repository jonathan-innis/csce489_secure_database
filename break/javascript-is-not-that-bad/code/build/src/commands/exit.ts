import { ADMIN, SECURITY_VIOLATION_STATUS } from '../constants';
import { addToStatuses, getCurrentPrincipal } from '../data';
import { setServerShouldExit } from '../server';

// If the command is exit, then the server outputs the status code is EXITING,
// terminates the client connection, and halts with return code 0 (and thus does not accept any more connections).
// This command is only allowed if the current principal is admin; otherwise it is a security violation.

export const exitCommand = (command: string) => {
    // console.log(`Running 'exit' command: '${command}'...`);

    if (getCurrentPrincipal() !== ADMIN) {
        addToStatuses({
            status: SECURITY_VIOLATION_STATUS
        });
        return;
    }

    setServerShouldExit();
};
