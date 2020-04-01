import net from 'net';
import tcpPortUsed from 'tcp-port-used';
// prettier-ignore
import { ADMIN, ANYONE, AS, EXIT_CODE, FAILURE_STATUS, INVALID_COMMAND_LINE_INPUT, PORT_TAKEN, STRINGEXPRESSION_NOQUOTES, THREE_STARS } from './constants';
import { createPrincipalData, StatusType, updateMasterData } from './data';
import { program } from './program';

const LOCALHOST = '127.0.0.1';

let serverShouldExit = false;
export const setServerShouldExit = () => {
    serverShouldExit = true;
};

/**
 * Start the server, setup admin password, setup functions to handle programs
 */
const startServer = async (port: number) => {
    try {
        const isPortUsed = await tcpPortUsed.check(port, LOCALHOST);
        if (isPortUsed) {
            process.exit(PORT_TAKEN);
        }
    } catch (error) {
        process.exit(INVALID_COMMAND_LINE_INPUT);
    }

    let dataStream = '';
    let timeoutTracker = false;

    const server = net.createServer(socket => {
        // TODO: only handle one client at a time (refuse other connections)
        socket.on('data', data => {
            dataStream += data;

            timeoutTracker = true;
            setTimeout(() => {
                if (timeoutTracker) {
                    const outputToClient: StatusType = {
                        status: 'TIMEOUT'
                    };
                    try {
                        socket.write(`${JSON.stringify(outputToClient)}\n`);
                        socket.destroy();
                    } catch (error) {
                        // probably timeout from successfull connection, don't do anything and assume we are smart coders
                    }
                }
            }, 30000);

            // remove bad data from the front (when socket opens)....assume 'as' is first part of program
            const indexOfAs = dataStream.indexOf(AS);
            if (indexOfAs !== -1) {
                dataStream = dataStream.slice(indexOfAs);
            }

            if (dataStream.includes(THREE_STARS)) {
                const indexOfStars = dataStream.indexOf(THREE_STARS);
                const programString = dataStream.substring(0, indexOfStars + THREE_STARS.length);

                // TODO: parse program and ensure conforms to the grammar (parse error takes precedence over all others....catch here!)

                if (programString.length > 1000000) {
                    const outputToClient: StatusType = {
                        status: FAILURE_STATUS
                    };
                    socket.write(`${JSON.stringify(outputToClient)}\n`);
                } else {
                    try {
                        program(programString, socket);
                    } catch (error) {
                        console.log(error);

                        const outputToClient: StatusType = {
                            status: FAILURE_STATUS
                        };
                        socket.write(`${JSON.stringify(outputToClient)}\n`);
                    }
                }

                dataStream = '';
                socket.destroy();

                if (serverShouldExit) {
                    process.exit(EXIT_CODE);
                }
            }
        });

        socket.on('close', () => {
            dataStream = '';
            timeoutTracker = false;
        });
    });

    // Start the server
    server.listen(port, LOCALHOST, () => {
        // console.log(`Server is now on and listening on port ${port}...`);
    });

    server.on('close', () => {
        // console.log('Server has closed.'); // not sure if this code is ever gracefully reached...
    });
};

/**
Command line arguments cannot exceed 4096 characters each
The port argument must be a number between 1,024 and 65,535 (inclusive). It should be provided in decimal without any leading 0's. Thus 1042 is a valid input number but the octal 052 or hexadecimal 0x2a are not.
The password argument, if present, must be a legal string s, per the rules for strings given above, but without the surrounding quotation marks.
 */

const { argv } = process;
// [0] = node, [1] = server, [2] = port, [3] = adminPass (optional)
if (argv.length !== 3 && argv.length !== 4) {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}

let adminPassword = ADMIN;

if (argv.length === 4) {
    // eslint-disable-next-line prefer-destructuring
    adminPassword = argv[3];
    // password is a proper string
    if (adminPassword.length > 65535) {
        process.exit(INVALID_COMMAND_LINE_INPUT);
    }
    if (!STRINGEXPRESSION_NOQUOTES.test(adminPassword)) {
        process.exit(INVALID_COMMAND_LINE_INPUT);
    }
}

createPrincipalData(ADMIN, adminPassword);
createPrincipalData(ANYONE, 'unspecified');
updateMasterData();
if (argv[2][0] === '0') {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}
// don't allow leading spaces
if (argv[2][0] === ' ') {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}
// don't allow trailing spaces
if (argv[2][argv[2].length - 1] === ' ') {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}
// don't allow ports out of range
if (Number(argv[2]) < 1024 || Number(argv[2]) > 65535) {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}
// arguments cannot be longer than 4096 characters
if (argv[0].length >= 4096 || argv[1].length >= 4096 || argv[2].length >= 4096) {
    process.exit(INVALID_COMMAND_LINE_INPUT);
}
// password is a proper string
// if (adminPassword.length !== adminPassword.match(STRINGEXPRESSION).length || adminPassword.length > 65535) {
//     process.exit(INVALID_COMMAND_LINE_INPUT);
// }
startServer(Number(argv[2]));
