import { getWorkingPrincipals, PrincipalsType, rollbackPrincipals } from './principals';
import { deleteLocalVariables, getWorkingVariables, rollbackVariables, VariablesType } from './variables';

export type FullDataType = {
    principals: PrincipalsType;
    variables: VariablesType;
};

/**
 * Validated and Correct Data, exists outside of unconfirmed transactions.
 */
const masterData: FullDataType = {
    principals: {},
    variables: {}
};
export const getMasterData = () => masterData;

/**
 * Transaction is complete, all changes now ready to put into master record.
 */
export const updateMasterData = () => {
    deleteLocalVariables();

    masterData.variables = JSON.parse(JSON.stringify(getWorkingVariables()));
    masterData.principals = JSON.parse(JSON.stringify(getWorkingPrincipals()));
};

/**
 * Working data goes back to whatever the masterData had.
 */
export const rollbackData = () => {
    rollbackPrincipals();
    rollbackVariables();
};

export type StatusType = {
    status: string;
    output?: any;
};

/**
 * List of status messages to send to the client once transaction is complete.
 */
let programStatuses: StatusType[] = [];
export const addToStatuses = (newStatus: StatusType) => {
    programStatuses.push(newStatus);
};
export const emptyProgramStatuses = () => {
    programStatuses = [];
};
export const getProgramStatuses = () => programStatuses;

/**
 * Global variable indicating if the program had a security violation.
 */
let hadSecurityViolation = false;
export const markHadSecurityViolation = () => {
    hadSecurityViolation = true;
};
export const clearHadSecurityViolation = () => {
    hadSecurityViolation = false;
};
export const getHadSecurityViolation = () => hadSecurityViolation;

/**
 * Global variable indicating if the program failed to parse data, or if command was invalid.
 */
let hadFailure = false;
export const markHadFailure = () => {
    hadFailure = true;
};
export const clearHadFailure = () => {
    hadFailure = false;
};
export const getHadFailure = () => hadFailure;
