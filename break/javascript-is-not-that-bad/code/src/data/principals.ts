import { ANYONE } from '../constants';
import { getMasterData } from './data';

/**
 * Name of principal currently executing the program.
 */
let currentPrincipal = '';
export const getCurrentPrincipal = () => currentPrincipal;
export const updateCurrentPrincipal = (newPrincipalName: string) => {
    currentPrincipal = newPrincipalName;
};

let defaultDelegator = ANYONE;
export const getDefaultDelegator = () => defaultDelegator;
export const updateDefaultDelegator = (newPrincipalName: string) => {
    defaultDelegator = newPrincipalName;
};

/**
 * principals['name'] = 'password'
 */
export type PrincipalsType = {
    [principalName: string]: string;
};

let workingPrincipals: PrincipalsType = {};
export const getWorkingPrincipals = () => workingPrincipals;

export const createPrincipalData = (name: string, password: string) => {
    workingPrincipals[`${name}`] = password;
};

export const changePasswordData = (name: string, password: string) => {
    workingPrincipals[`${name}`] = password;
};

export const rollbackPrincipals = () => {
    workingPrincipals = JSON.parse(JSON.stringify(getMasterData().principals));
};
