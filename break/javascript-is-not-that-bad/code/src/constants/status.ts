/**
 * These are status codes sent to client from server when commands execute.
 */

export const RETURNING_STATUS = 'RETURNING';
export const SECURITY_VIOLATION_STATUS = 'DENIED';
export const FAILURE_STATUS = 'FAILED';
export const EXIT_STATUS = 'EXITING';

export const CREATE_PRINCIPAL_STATUS = 'CREATE_PRINCIPAL';
export const CHANGE_PASSWORD_STATUS = 'CHANGE_PASSWORD';
export const SET_STATUS = 'SET';
export const APPEND_STATUS = 'APPEND';
export const LOCAL_STATUS = 'LOCAL';
export const FOREACH_STATUS = 'FOREACH';
export const SET_DELEGATION_STATUS = 'SET_DELEGATION';
export const DELETE_DELEGATION = 'DELETE_DELEGATION';
export const DEFAULT_DELEGATOR = 'DEFAULT_DELEGATOR';
