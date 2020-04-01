/**
<program> ::= as principal p password s do \n <command> ***

<command> ::= exit \n | return <expression> \n | <primitive_command> \n <command>

<expression> ::=  <value> | [] | { <field_values> }

<field_values> ::=  x = <value> | x = <value> , <field_values>

<value> ::=  x | x . y | s

<primitive_command> ::=
          create principal p s
        | change password p s
        | set x = <expression>
        | append to x with <expression>
        | local x = <expression>
        | foreach y in x replacewith <expression>
        | set delegation <tgt> q <right> -> p
        | delete delegation <tgt> q <right> -> p
        | default delegator = p

<tgt> ::= all | x

<right> ::= read | write | append | delegate
*/

export const ADMIN = 'admin';
export const ANYONE = 'anyone';

export const ALL = 'all';
export const APPEND = 'append';
export const AS = 'as';
export const CHANGE = 'change';
export const CREATE = 'create';
export const DEFAULT = 'default';
export const DELEGATE = 'delegate';
export const DELEGATION = 'delegation';
export const DELEGATOR = 'delegator';
export const DELETE = 'delete';
export const DO = 'do';
export const EXIT = 'exit';
export const FOREACH = 'foreach';
export const IN = 'in';
export const LOCAL = 'local';
export const PASSWORD = 'password';
export const PRINCIPAL = 'principal';
export const READ = 'read';
export const REPLACEWITH = 'replacewith';
export const RETURN = 'return';
// eslint-disable-next-line no-useless-escape
export const STRINGEXPRESSION = /^[\"][A-Za-z0-9_ ,;\.?!-]*[\"]$/;
// eslint-disable-next-line no-useless-escape
export const STRINGEXPRESSION_NOQUOTES = /^[A-Za-z0-9_ ,;\.?!-]*$/;
export const IDENTIFIEREXPRESSION = /^[A-Za-z][A-Za-z0-9_]*$/;
// eslint-disable-next-line no-useless-escape
export const COMMENTREGEX = /^[\/][\/][A-Za-z0-9_ ,;\.?!-]*$/;
export const SET = 'set';
export const TO = 'to';
export const WRITE = 'write';
export const THREE_STARS = '***';
export const SPLIT = 'split';
export const CONCAT = 'concat';
export const TOLOWER = 'tolower';
export const NOTEQUAL = 'notequal';
export const EQUAL = 'equal';
export const FILTEREACH = 'filtereach';
export const WITH = 'with';
export const LET = 'let';

export const RESERVED_WORDS: string[] = [
    ALL,
    APPEND,
    AS,
    CHANGE,
    CREATE,
    DEFAULT,
    DELEGATE,
    DELEGATION,
    DELEGATOR,
    DELETE,
    DO,
    EXIT,
    FOREACH,
    IN,
    LOCAL,
    PASSWORD,
    PRINCIPAL,
    READ,
    REPLACEWITH,
    RETURN,
    SET,
    TO,
    WRITE,
    THREE_STARS,
    SPLIT,
    CONCAT,
    TOLOWER,
    NOTEQUAL,
    EQUAL,
    FILTEREACH,
    WITH,
    LET
];
