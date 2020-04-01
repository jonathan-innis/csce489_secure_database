import { ADMIN, ANYONE } from '../constants';
import { getMasterData } from './data';

export type VarType = 'list' | 'string' | 'record';

export type RightType = 'read' | 'write' | 'append' | 'delegate';

export type VariableDataType = {
    isLocal: boolean;
    value: any;
    varType: VarType;
    read: {
        [principal: string]: string[]; // 'spencer': (got permission from) ['admin']
    };
    write: {
        [principal: string]: string[]; // 'spencer': (got permission from) ['admin']
    };
    append: {
        [principal: string]: string[]; // 'spencer': (got permission from) ['admin']
    };
    delegate: {
        [principal: string]: string[]; // 'spencer': (got permission from) ['admin']
    };
    [namedIndex: string]: any;
};

/**
 * variables['varname'] = {} -> varDataObject
 */
export type VariablesType = {
    [varName: string]: VariableDataType;
};

let workingVariables: VariablesType = {};
export const getWorkingVariables = () => workingVariables;

export const addVariable = (name: string, value: any, varType: VarType) => {
    workingVariables[`${name}`] = {
        value,
        isLocal: false,
        varType,
        read: {},
        write: {},
        append: {},
        delegate: {}
    };
};

export const setLocal = (name: string) => {
    workingVariables[`${name}`].isLocal = true;
};

export const setVariableValue = (varname: string, varValue: any, varType: VarType) => {
    workingVariables[`${varname}`].value = varValue;
    workingVariables[`${varname}`].varType = varType;
};

export const hasPermissionTo = (varName: string, principalName: string, right: RightType) => {
    const listOfPincipalsToCheck = [ANYONE, principalName];
    while (listOfPincipalsToCheck.length !== 0) {
        const currentPrincipalToCheck = listOfPincipalsToCheck.pop();

        // base case
        if (currentPrincipalToCheck === ADMIN) return true;

        // parent we are currently checking doesn't have rights
        if (!workingVariables[`${varName}`][`${right}`][`${currentPrincipalToCheck}`]) continue;

        // add it's parents to the list to check
        for (const parentPrincipal of workingVariables[`${varName}`][`${right}`][`${currentPrincipalToCheck}`]) {
            listOfPincipalsToCheck.push(parentPrincipal);
        }
    }

    // none of our checks were true (no admin)
    return false;
};

// prettier-ignore
export const delegateData = (varName: string, principalTakingRights: string, principalGivingRights: string, right: RightType) => {
    if (workingVariables[`${varName}`][`${right}`][`${principalTakingRights}`] === undefined) {
        workingVariables[`${varName}`][`${right}`][`${principalTakingRights}`] = [];
    }
    workingVariables[`${varName}`][`${right}`][`${principalTakingRights}`].push(principalGivingRights);
};

// prettier-ignore
export const undelegateData = (varName: string, principalLosingRights: string, principalTakingRights: string, right: RightType) => {
    if (principalLosingRights === principalTakingRights) {
        delete workingVariables[`${varName}`][`${right}`][`${principalLosingRights}`];
        return;
    }
    workingVariables[`${varName}`][`${right}`][`${principalLosingRights}`] = workingVariables[`${varName}`][`${right}`][`${principalLosingRights}`].filter(
        (principalThatGaveRights: string) => principalThatGaveRights !== principalTakingRights
    );
    if (workingVariables[`${varName}`][`${right}`][`${principalLosingRights}`].length === 0) {
        delete workingVariables[`${varName}`][`${right}`][`${principalLosingRights}`];
    }
};

export const rollbackVariables = () => {
    workingVariables = JSON.parse(JSON.stringify(getMasterData().variables));
};

export const updateWorkingVariables = (newWorkingVariables: VariablesType) => {
    workingVariables = JSON.parse(JSON.stringify(newWorkingVariables));
};

export const deleteLocalVariables = () => {
    for (const varname of Object.keys(workingVariables)) {
        if (workingVariables[`${varname}`].isLocal) {
            delete workingVariables[`${varname}`];
        }
    }
};
