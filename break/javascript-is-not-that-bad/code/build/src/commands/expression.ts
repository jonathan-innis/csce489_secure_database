// get the value of an expression

import { ADMIN, STRINGEXPRESSION, IDENTIFIEREXPRESSION, RESERVED_WORDS, SPLIT, CONCAT, TOLOWER } from '../constants';
// prettier-ignore
import { getCurrentPrincipal, getWorkingVariables, markHadFailure, markHadSecurityViolation, VarType, hasPermissionTo } from '../data';

export const evalExpression = (expression: string, foreachVarname: string | null, foreachVarValue: any | null): { value: any; varType: VarType } => {
    // x = []
    if (expression[0] === '[') {
        return {
            value: [],
            varType: 'list'
        };
    }

    // x = "string"
    if (expression[0] === '"') {
        // add 2 due to quotes
        if (!STRINGEXPRESSION.test(expression)) {
            markHadFailure();
            return null;
        }

        if (expression.length > 65535 + 2) {
            markHadFailure();
            return null;
        }
        // console.log(expression.length);

        return {
            value: expression.substring(1, expression.length - 1),
            varType: 'string'
        };
    }

    if (expression.indexOf(SPLIT) === 0) {
        // return {};
    }

    if (expression.indexOf(CONCAT) === 0) {
        // return {};
    }

    if (expression.indexOf(TOLOWER) === 0) {
        // return {};
    }

    // x = { field = values }
    if (expression[0] === '{') {
        const varObject: { [key: string]: string } = {};

        expression = expression.slice(expression.indexOf('{') + '{'.length, expression.indexOf('}')).trim();

        // console.log(expression);

        // loop through all the fields and handle accordingly
        const fields: string[] = [];
        while (expression.includes(',')) {
            const singleField = expression.substring(0, expression.indexOf(',')).trim();
            fields.push(singleField.trim());
            expression = expression.slice(expression.indexOf(',') + ','.length).trim();
        }
        // push the last one
        fields.push(expression.trim());

        // console.log(fields);

        for (const field of fields) {
            const nameOfField = field.substring(0, field.indexOf('=')).trim();
            if (!IDENTIFIEREXPRESSION.test(nameOfField) || nameOfField.length > 255) {
                markHadFailure();
                return null;
            }

            if (RESERVED_WORDS.includes(nameOfField)) {
                markHadFailure();
                return null;
            }
            // console.log(nameOfField);

            const valueOfField = field.slice(field.indexOf('=') + '='.length).trim();
            // console.log(valueOfField);

            if (Object.keys(varObject).includes(nameOfField)) {
                // console.log('hey already existed in record');
                markHadFailure();
                return null;
            }

            // { x = "string" }
            if (valueOfField[0] === '"') {
                if (!STRINGEXPRESSION.test(valueOfField) || valueOfField.length > 65535 + 2) {
                    markHadFailure();
                    return null;
                }
                varObject[`${nameOfField}`] = valueOfField.substring(1, valueOfField.length - 1);
                continue;
            }

            // { x = y.z }
            if (valueOfField.includes('.')) {
                // do they have read on y?
                const whyVar = valueOfField.substring(0, valueOfField.indexOf('.')).trim();
                const zeeVar = valueOfField.substring(valueOfField.indexOf('.') + '.'.length, valueOfField.length);

                if (whyVar === foreachVarname) {
                    // foreach item in list replacewith { field = item.thing }
                    // item is not a variable stored in the system, but rather a temp working thing we throw around to represnet current item in the list
                    try {
                        varObject[`${nameOfField}`] = JSON.parse(JSON.stringify(foreachVarValue[`${zeeVar}`]));
                    } catch (error) {
                        markHadFailure();
                        return null;
                    }
                    continue;
                }

                if (!getWorkingVariables()[`${whyVar}`]) {
                    // console.log('failed due to var not existing');
                    markHadFailure();
                    return null;
                }
                if (
                    getWorkingVariables()[`${whyVar}`].varType !== 'record' ||
                    !Object.keys(getWorkingVariables()[`${whyVar}`].value).includes(zeeVar)
                ) {
                    markHadFailure();
                    return null;
                }
                if (!hasPermissionTo(whyVar, getCurrentPrincipal(), 'read') && getCurrentPrincipal() !== ADMIN) {
                    markHadSecurityViolation();
                    return null;
                }

                // deep copy the string
                varObject[`${nameOfField}`] = JSON.parse(JSON.stringify(getWorkingVariables()[`${whyVar}`].value[`${zeeVar}`]));
                continue;
            }

            // { x = y }
            if (valueOfField === foreachVarname) {
                varObject[`${nameOfField}`] = JSON.parse(JSON.stringify(foreachVarValue));
                continue;
            }

            if (!getWorkingVariables()[`${valueOfField}`]) {
                markHadFailure();
                return null;
            }
            if (getWorkingVariables()[`${valueOfField}`].varType !== 'string') {
                markHadFailure();
                return null;
            }
            if (!hasPermissionTo(valueOfField, getCurrentPrincipal(), 'read') && getCurrentPrincipal() !== ADMIN) {
                markHadSecurityViolation();
                return null;
            }

            varObject[`${nameOfField}`] = JSON.parse(JSON.stringify(getWorkingVariables()[`${valueOfField}`].value));
        }

        return {
            value: varObject,
            varType: 'record'
        };
    }

    // x = y.z
    if (expression.includes('.')) {
        // x = y.z -> all field values are strings, so good to assume that
        const whyVar = expression.substring(0, expression.indexOf('.')).trim();
        const zeeVar = expression.substring(expression.indexOf('.') + '.'.length, expression.length);
        if (!getWorkingVariables()[`${whyVar}`]) {
            markHadFailure();
            return null;
        }
        if (getWorkingVariables()[`${whyVar}`].varType !== 'record' || !Object.keys(getWorkingVariables()[`${whyVar}`].value).includes(zeeVar)) {
            markHadFailure();
            return null;
        }
        if (!hasPermissionTo(whyVar, getCurrentPrincipal(), 'read') && getCurrentPrincipal() !== ADMIN) {
            markHadSecurityViolation();
            return null;
        }

        // deep copy the string
        return {
            value: JSON.parse(JSON.stringify(getWorkingVariables()[`${whyVar}`].value[`${zeeVar}`])),
            varType: 'string'
        };
    }

    // only option left
    // x = y
    if (!getWorkingVariables()[`${expression}`]) {
        markHadFailure();
        return null;
    }
    if (!hasPermissionTo(expression, getCurrentPrincipal(), 'read') && getCurrentPrincipal() !== ADMIN) {
        markHadSecurityViolation();
        return null;
    }

    return {
        value: JSON.parse(JSON.stringify(getWorkingVariables()[`${expression}`].value)),
        varType: getWorkingVariables()[`${expression}`].varType
    };
};
