import { Socket } from 'net';
// prettier-ignore
import { appendToCommand, changePasswordCommand, createPrincipalCommand, defaultDelegatorCommand, deleteDelegationCommand, exitCommand, foreachCommand, localCommand, returnCommand, setCommand, setDelegationCommand } from './commands';
// prettier-ignore
import { APPEND, CHANGE, CREATE, DEFAULT, DELEGATION, DELEGATOR, DELETE, DO, EXIT, FAILURE_STATUS, FOREACH, LOCAL, PASSWORD, PRINCIPAL, RETURN, SECURITY_VIOLATION_STATUS, SET, TO, ANYONE, COMMENTREGEX } from './constants';
// prettier-ignore
import { clearHadFailure, clearHadSecurityViolation, emptyProgramStatuses, getHadFailure, getHadSecurityViolation, getProgramStatuses, getWorkingPrincipals, markHadFailure, rollbackData, StatusType, updateCurrentPrincipal, updateMasterData } from './data';

const COMMAND_DELIMITER = '\n';

// TODO: actually parse the program.... -> Cason...
const isValidCommandSimpleCheck = (command: string) => {
    if (command.trim().indexOf('//') === 0) {
        return true;
    }

    // get rid of comment at the end of the line
    const indexOfComment = command.indexOf('//');
    if (indexOfComment !== -1) {
        command = command.substring(0, indexOfComment);
    }

    if (command.trim().indexOf(EXIT) === 0) {
        return true;
    }

    if (command.trim().indexOf(RETURN) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(CREATE) === 0 && command.trim().slice(CREATE.length).trim().indexOf(PRINCIPAL) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(CHANGE) === 0 && command.trim().slice(CHANGE.length).trim().indexOf(PASSWORD) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(SET) === 0 && command.trim().slice(SET.length).trim().indexOf(DELEGATION) === 0) {
        return true;
    }

    // 'set' also found in 'set delegation' so check last
    if (command.trim().indexOf(SET) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(APPEND) === 0 && command.trim().slice(APPEND.length).trim().indexOf(TO) === 0) {
        return true;
    }

    if (command.trim().indexOf(LOCAL) === 0) {
        return true;
    }

    if (command.trim().indexOf(FOREACH) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(DELETE) === 0 && command.trim().slice(DELETE.length).trim().indexOf(DELEGATION) === 0) {
        return true;
    }

    // prettier-ignore
    if (command.trim().indexOf(DEFAULT) === 0 && command.trim().slice(DEFAULT.length).trim().indexOf(DELEGATOR) === 0) {
        return true;
    }

    return false;
};

/**
 * <program> ::= as principal p password s do \n <command> ***
 */
export const program = (programString: string, socket: Socket) => {
    // console.log('starting a program');

    programString = programString.slice(programString.indexOf(PRINCIPAL) + PRINCIPAL.length).trim(); // puts the name at the front

    const asPrincipalName = programString.substring(0, programString.indexOf(PASSWORD)).trim();

    if (asPrincipalName === ANYONE) {
        const securityViolation: StatusType = {
            status: SECURITY_VIOLATION_STATUS
        };
        socket.write(JSON.stringify(securityViolation));
        return;
    }

    programString = programString.slice(programString.indexOf(PASSWORD) + PASSWORD.length).trim(); // puts the password at the front

    const givenPrincipalPassword = programString.substring(1, programString.indexOf(' ') - 1); // password should have space after last quote

    // Did not find principal
    if (getWorkingPrincipals()[`${asPrincipalName}`] === undefined) {
        const failure: StatusType = {
            status: FAILURE_STATUS
        };
        socket.write(JSON.stringify(failure));
        return;
    }

    // password did not match
    if (getWorkingPrincipals()[`${asPrincipalName}`] !== givenPrincipalPassword) {
        const securityViolation: StatusType = {
            status: SECURITY_VIOLATION_STATUS
        };
        socket.write(JSON.stringify(securityViolation));
        return;
    }

    updateCurrentPrincipal(asPrincipalName);

    programString = programString.slice(programString.indexOf(DO) + DO.length).trim(); // trim cuts leading \n as well as whitespace

    // console.log('creating list of commands');

    const commands: string[] = [];
    while (programString.includes(COMMAND_DELIMITER)) {
        const singleCommand = programString.substring(0, programString.indexOf(COMMAND_DELIMITER)).trim();
        commands.push(singleCommand);
        programString = programString.slice(programString.indexOf(COMMAND_DELIMITER) + COMMAND_DELIMITER.length);
    }

    // console.log('starting to simple parse commands');

    for (const command of commands) {
        if (!isValidCommandSimpleCheck(command)) {
            markHadFailure();
            break;
        }
    }

    // console.log('starting to run each command');

    for (let command of commands) {
        if (getHadFailure() || getHadSecurityViolation()) {
            break;
        }

        // comment line on its own
        if (command.trim().indexOf('//') === 0) {
            if (!COMMENTREGEX.test(command)) {
                markHadFailure();
                break;
            }
            continue;
        }

        // get rid of comment at the end of the line
        const indexOfComment = command.indexOf('//');
        if (indexOfComment !== -1) {
            const comment = command.substring(indexOfComment, command.length - 1);
            if (!COMMENTREGEX.test(comment)) {
                markHadFailure();
                break;
            }
            command = command.substring(0, indexOfComment);
        }

        if (command.trim().indexOf(EXIT) === 0) {
            exitCommand(command.trim());
            break; // break instead of continue? (makes sense for these 2 end commands)
        }

        if (command.trim().indexOf(RETURN) === 0) {
            returnCommand(command.trim());
            break;
        }

        // prettier-ignore
        if (command.trim().indexOf(CREATE) === 0 && command.trim().slice(CREATE.length).trim().indexOf(PRINCIPAL) === 0) {
            createPrincipalCommand(command.trim());
            continue;
        }

        // prettier-ignore
        if (command.trim().indexOf(CHANGE) === 0 && command.trim().slice(CHANGE.length).trim().indexOf(PASSWORD) === 0) {
            changePasswordCommand(command.trim());
            continue;
        }

        // prettier-ignore
        if (command.trim().indexOf(SET) === 0 && command.trim().slice(SET.length).trim().indexOf(DELEGATION) === 0) {
            setDelegationCommand(command.trim());
            continue;
        }

        // 'set' also found in 'set delegation' so check last
        if (command.trim().indexOf(SET) === 0) {
            setCommand(command.trim());
            continue;
        }

        // prettier-ignore
        if (command.trim().indexOf(APPEND) === 0 && command.trim().slice(APPEND.length).trim().indexOf(TO) === 0) {
            appendToCommand(command.trim());
            continue;
        }

        if (command.trim().indexOf(LOCAL) === 0) {
            localCommand(command.trim());
            continue;
        }

        if (command.trim().indexOf(FOREACH) === 0) {
            foreachCommand(command.trim());
            continue;
        }

        // prettier-ignore
        if (command.trim().indexOf(DELETE) === 0 && command.trim().slice(DELETE.length).trim().indexOf(DELEGATION) === 0) {
            deleteDelegationCommand(command.trim());
            continue;
        }

        // prettier-ignore
        if (command.trim().indexOf(DEFAULT) === 0 && command.trim().slice(DEFAULT.length).trim().indexOf(DELEGATOR) === 0) {
            defaultDelegatorCommand(command.trim());
            continue;
        }

        markHadFailure(); // not reached if properly parsed
    }

    if (getHadFailure()) {
        const outputToClient: StatusType = {
            status: FAILURE_STATUS
        };
        socket.write(`${JSON.stringify(outputToClient)}\n`);
        clearHadFailure();
        rollbackData();
        emptyProgramStatuses();
        return;
    }

    if (getHadSecurityViolation()) {
        const outputToClient: StatusType = {
            status: SECURITY_VIOLATION_STATUS
        };
        socket.write(`${JSON.stringify(outputToClient)}\n`);
        clearHadSecurityViolation();
        rollbackData();
        emptyProgramStatuses();
        return;
    }

    // after loop is done, ready to return all the statuses to client
    let totalOutputToClient = '';
    for (const status of getProgramStatuses()) {
        totalOutputToClient += JSON.stringify(status);
        totalOutputToClient += '\n';
    }

    socket.write(totalOutputToClient);

    // no need to rollback, store changes in master
    updateMasterData();
    emptyProgramStatuses();
};
