from DataStore import DataVariable, DelegationType, DataStore, Principal
from commands import *
from copy import deepcopy

class SecurityViolationException(Exception):
    pass

class FailureException(Exception):
    pass

# class ExitException(Exception):
#     pass

class DataServer:

    def __init__(self, admin_password: str ='admin'):

        self.data_map = DataStore()
        self.principal_map = DataStore({
            'admin': Principal(admin_password),
            'anyone': Principal(None)
        })

        self.default_delegator_id = 'anyone' # anyone
        # self.executing_principal = None

    def __del__(self):
        del self.data_map
        del self.principal_map
        del self.default_delegator_id

    def __evaluate_expression(self, executing_principal_id, expression):
        
        evaluated_expression = None
        if type(expression) is Record:
            record_dict = expression.items
            evaluated_expression = {}
            for field, record_item in record_dict.items():
                record_item_expression = record_item.value
                new_value = self.__evaluate_expression(executing_principal_id, record_item_expression)
                if (type(new_value) is not str):
                    raise FailureException('record contents can only be string')
                evaluated_expression[field] = new_value
        elif type(expression) is Identifier:
            variable_id = expression.value

            if variable_id in self.data_map:
                variable = self.data_map[variable_id]
                if not variable.is_delegated_to(executing_principal_id, DelegationType.READ):
                    raise SecurityViolationException(f'Executing principal {executing_principal_id} lacks read delegation to {variable_id}')
                evaluated_expression = deepcopy(variable.value)
            else:
                raise FailureException(f'Variable {variable_id} is not defined')
        
        elif type(expression) is RecordIdentifier:
            record_variable_id = expression.recordName
            record_field_id = expression.recordKey

            if record_variable_id in self.data_map:
                if record_field_id in self.data_map[record_variable_id].value:
                    evaluated_expression = self.data_map[record_variable_id].value[record_field_id]
                else:
                    raise FailureException(f'Field {record_field_id} not found in record {record_variable_id}')
            else:
                raise FailureException(f'Variable {record_variable_id} is not defined')
        elif type(expression) is Value:
            evaluated_expression = expression.value
        elif type(expression) is NewArray:
            evaluated_expression = []
        else:
            pass # throw exception: error

        return evaluated_expression

    def __create_principal(self, executing_principal_id, principal_id, password):
        # Fails if p already exists as a principal.
        # Security violation if the current principal is not admin.
        if principal_id in self.principal_map:
            raise FailureException(f'Principal {principal_id} already exists')
            # throw exception: Fail
        
        executing_principal = self.principal_map[executing_principal_id]
        if executing_principal is not self.principal_map['admin']:
            raise SecurityViolationException(f'Executing principal {executing_principal_id} is not admin')
            # throw exception: Security

        self.principal_map.set_value(principal_id, Principal(password))
        new_principal = self.principal_map[principal_id]
        default_delegator = self.principal_map[self.default_delegator_id]

        for key, variable in default_delegator.can_delegate_variables.items():
            variable.add_delegation(self.default_delegator_id, principal_id, DelegationType.READ)
            variable.add_delegation(self.default_delegator_id, principal_id, DelegationType.WRITE)
            variable.add_delegation(self.default_delegator_id, principal_id, DelegationType.APPEND)
            variable.add_delegation(self.default_delegator_id, principal_id, DelegationType.DELEGATE)
            new_principal.can_delegate_variables[key] = variable
        

    def __change_password(self, executing_principal_id, principal_id, new_password):
        # Fails if p does not exist
        # Security violation if the current principal is neither admin nor p itself.
        if principal_id not in self.principal_map:
            raise FailureException(f'Principal {principal_id} does not exist')
            # throw exception: Fail

        principal_to_change = self.principal_map[principal_id]
        executing_principal = self.principal_map[executing_principal_id]
        if not (executing_principal is self.principal_map['admin'] or
                executing_principal is principal_to_change):
            raise SecurityViolationException(f'Executing principal is not admin or the principal whose password is being changed ({principal_id})')
            # throw exception: Security
        
        principal_to_change.password = new_password

    def __set_value(self, executing_principal_id, variable_id, expression):
        # May fail or have a security violation due to evaluating <expr>
        # Security violation if the current principal does not have write permission on x.
        new_value = self.__evaluate_expression(executing_principal_id, expression)
        executing_principal = self.principal_map[executing_principal_id]

        if variable_id in self.data_map:
            variable = self.data_map[variable_id]
            if not (variable.is_delegated_to(executing_principal_id, DelegationType.WRITE) or
                    self.data_map.is_local(variable_id)):
                raise SecurityViolationException(f'Executing principal {executing_principal_id} does not have permission to write to {variable_id}')
                # throw exception: Security
            variable.value = new_value
            
        else:
            new_variable = DataVariable(executing_principal_id, new_value)
            self.data_map.set_value(variable_id, new_variable)
            executing_principal.can_delegate_variables[variable_id] = new_variable

    def __append_to_list(self, executing_principal_id, variable_id, expression):
        # Fails if x is not defined
        # Security violation if the current principal does not have either write or append permission on x (read permission is not necessary).
        # Fails if x is not a list
        # May fail or have a security violation due to evaluating <expr>
        if variable_id not in self.data_map:
            raise FailureException(f'Variable {variable_id} does not exist')
            # throw exception: Fail
        
        variable = self.data_map[variable_id]
        executing_principal = self.principal_map[executing_principal_id]
        if not (variable.is_delegated_to(executing_principal_id, DelegationType.WRITE) or
                variable.is_delegated_to(executing_principal_id, DelegationType.APPEND)):
            raise SecurityViolationException(f'Executing principal {executing_principal_id} does not have write or append delegation on {variable_id}')
            # throw exception: Security
        
        if type(variable.value) is not list:
            raise FailureException(f'Variable {variable_id} is not a list')
            # throw exception: Fail

        new_value_to_append = self.__evaluate_expression(executing_principal_id, expression)
        # if not isinstance(new_value_to_append, (str, dict)):
        #     raise FailureException(f'Expression {expression} does no evaluate to string or record')
        #     # throw exception: Fail
        if type(new_value_to_append) is list:
            variable.value += new_value_to_append
        elif isinstance(new_value_to_append, (str, dict)):
            variable.value.append(new_value_to_append)
        else:
            pass # throw exception: error


        
    
    def __set_local(self, executing_principal_id, variable_id, expression):
        # Fails if x is already defined as a local or global variable.
        # May fail or have a security violation due to evaluating <expr>
        if variable_id in self.data_map:
            raise FailureException(f'Variable {variable_id} already exists')
            # throw exception: fail
        new_value = self.__evaluate_expression(executing_principal_id, expression)
        self.data_map.set_value(variable_id, DataVariable(executing_principal_id, new_value), True)

    def __set_delegation(self, executing_principal_id, delegator_principal_id, delegatee_principal_id, variable_id, delegation_type):
        # Fails if either p or q does not exist
        # Fails if x does not exist or if it is a local variable, if <tgt> is a variable x.
        # Security violation unless the current principal is admin or q; if the principal is q and <tgt> is the variable x, then q must have delegate permission on

        if not (delegator_principal_id in self.principal_map and
                delegatee_principal_id in self.principal_map):
            raise FailureException(f'Delegator {delegator_principal_id} or delegatee {delegatee_principal_id} does not exist')
            # throw exception: fail

        if variable_id not in self.data_map or self.data_map.is_local(variable_id):
            raise FailureException(f'Variable {variable_id} does not exist or is a local')
            # throw exception: fail
        
        delegator_principal = self.principal_map[delegator_principal_id]
        delegatee_principal = self.principal_map[delegatee_principal_id]
        executing_principal = self.principal_map[executing_principal_id]
        if not (executing_principal is self.principal_map['admin'] or
                executing_principal is delegator_principal):
            raise SecurityViolationException(f'Executing principal {executing_principal_id} is not admin or delegator')
            # throw exception: Security
        variable = self.data_map[variable_id]
        if not variable.is_delegated_to(executing_principal_id, DelegationType.DELEGATE):
            raise SecurityViolationException(f'Executing principal {executing_principal_id} does not have delegation privilage')
            # throw exception: Security

        variable.add_delegation(delegator_principal_id, delegatee_principal_id, delegation_type)
        if delegation_type == DelegationType.DELEGATE:
            delegatee_principal.can_delegate_variables[variable_id] = variable
    
    def __delete_delegation(self, executing_principal_id, delegator_principal_id, delegatee_principal_id, variable_id, delegation_type):
        # Fails if either p or q does not exist
        # Fails if x does not exist or if it is a local variable, if <tgt> is a variable x.
        # Security violation unless the current principal is admin, p, or q; if the principal is q and <tgt> is a variable x, then it must have delegate permission on x. 
        #  (No special permission is needed if the current principal is p: any non-admin principal can always deny himself rights).
        if not (delegator_principal_id in self.principal_map and
                delegatee_principal_id in self.principal_map):
            raise FailureException(f'Delegator {delegator_principal} or delegatee {delegatee_principal_id} does not exist')
            # throw exception: fail

        if variable_id not in self.data_map or self.data_map.is_local(variable_id):
            raise FailureException(f'Variable {variable_id} does not exist or is a local')
            # throw exception: fail
        delegator_principal = self.principal_map[delegator_principal_id]
        delegatee_principal = self.principal_map[delegatee_principal_id]
        executing_principal = self.principal_map[executing_principal_id]
        if not (executing_principal is self.principal_map['admin'] or
                executing_principal is delegator_principal or
                executing_principal is delegatee_principal):
            raise SecurityViolationException(f'Executing principal {executing_principal_id} is not admin, delegator or delegatee')
            # throw exception: Security
        variable = self.data_map[variable_id]
        if not variable.is_delegated_to(executing_principal_id, DelegationType.DELEGATE):
            raise SecurityViolationException(f'Executing principal {executing_principal_id} does not have delegation privilage')
            # throw exception: Security
        
        if delegation_type == DelegationType.DELEGATE:
            del delegatee_principal.can_delegate_variables[variable_id]

        variable.remove_delegation(delegator_principal_id, delegatee_principal_id, delegation_type)
        if delegation_type == DelegationType.DELEGATE:
            del delegatee_principal.can_delegate_variables[variable_id]


    def __set_default_delegator(self, executing_principal_id, default_delegator_id):
        # Fails if p does not exist
        # Security violation if the current principal is not admin.
        if default_delegator_id not in self.principal_map:
            raise FailureException(f'Principal {default_delegator_id} does not exist')
            # throw exception: Fail

        executing_principal = self.principal_map[executing_principal_id]
        if executing_principal is not self.principal_map['admin']:
            raise FailureException(f'Principal {executing_principal_id} is not admin')
            # throw exception: Security

        self.default_delegator_id = default_delegator_id        

    def __for_each_replace_constant(self, executing_principal_id, container_id, iter_item_id, expression):
        # Fails if x is not defined
        # Security violsecurityation if the current principal does not have read and write permission on x.
        # Fails if y is already defined as a local or global variable.
        # Fails if x is not a list.
        # If any execution of <expr> fails or has a security violation, then entire foreach does. <expr> is from the front of the list to the back
        # Fails if <expr> evaluates to a list, rather than a string or a record.

        if container_id not in self.data_map:
            raise FailureException(f'Variable {container_id} does not exist')
            # throw exception: Fail
        container_variable = self.data_map[container_id]

        if not (container_variable.is_delegated_to(executing_principal_id, DelegationType.READ) and
                container_variable.is_delegated_to(executing_principal_id, DelegationType.WRITE)):
            raise SecurityViolationException(f'Principal {executing_principal_id} does not have read and write delegation to {container_variable_id}')
            # throw exception: Security
        
        if iter_item_id in self.data_map:
            raise FailureException(f'{iter_item_id} exists as a variable')
            # throw exception: fail
        
        if type(container_variable.value) is not list:
            raise FailureException(f'Variable {container_variable_id} is not list')
            # throw exception: fai;


        if type(expression) is IncompleteRecord:
            known_value = self.__evaluate_expression(executing_principal_id, expression.completeRecord)

            if type(known_value) is not dict:
                raise TypeError(f'{type(expression.completeRecord)} {type(known_value)}') # error on our part
            
            for index, item in enumerate(container_variable.value):
                value_to_insert = known_value
                for field_id in expression.incompleteKeys:
                    value_to_insert[field_id] = container_variable.value[index]
                container_variable.value[index] = value_to_insert.copy()

        else:
            value_to_insert = self.__evaluate_expression(executing_principal_id, expression)

            if not isinstance(value_to_insert, (dict, str)):
                raise FailureException(f'Expressiorecn {value_to_insert} is not list or string')
                # throw exception: fail
            
            for index, item in enumerate(container_variable.value):
                container_variable.value[index] = value_to_insert


    def __for_each_replace_field_val(self, executing_principal_id, container_id, iter_item_id, expression):
        # Fails if x is not defined
        # Security violation if the current principal does not have read and write permission on x.
        # Fails if y is already defined as a local or global variable.
        # Fails if x is not a list.
        # If any execution of <expr> fails or has a security violation, then entire foreach does. <expr> is from the front of the list to the back
        # Fails if <expr> evaluates to a list, rather than a string or a record.

        container_variable = self.data_map[container_id]

        if not (container_variable.is_delegated_to(executing_principal_id, DelegationType.READ) and
                container_variable.is_delegated_to(executing_principal_id, DelegationType.WRITE)):
            raise SecurityViolationException(f'Principal {executing_principal_id} does not have read and write delegation to {container_variable_id}')
            # throw exception: Security
        
        if iter_item_id in self.data_map:
            raise FailureException(f'{iter_item_id} exists as a variable') 
            # throw exception: fail
        
        if type(container_variable.value) is not list:
            raise FailureException(f'Variable {container_variable_id} is not list') 
            # throw exception: fail

        field_id = expression.recordKey
        for index, record in enumerate(container_variable.value):
            if type(record) is not dict:
                raise FailureException(f'Variable in {container_variable_id} is not a record') 
                # throw exception: fail
            if field_id not in record:
                raise FailureException(f'Record in {container_variable_id} does not contain {field_id}')
                # throw exception: fail
            container_variable.value[index] = record[field_id]        

    def execute_commands(self, commands: list) -> list:

        if type(commands[0]) is not Login:
            pass # throw exception: Error
        if not isinstance(commands[-1], (ReturnValue, Exit)):
            pass # throw exception: Error
        
        executing_principal_id = commands[0].identifier.value
        executing_principal_password = commands[0].password.value
        if executing_principal_id not in self.principal_map:
            return [{'status': 'FAILED'}]
        executing_principal = self.principal_map[executing_principal_id]
        if executing_principal.password != executing_principal_password:
            return [{'status': 'DENIED'}]
        

        status_codes = []

        for command in commands:
            # print(type(command))
            # if type(command) is not Local:
            #     print(type(command))

            try:
                if type(command) is CreatePrincipal:
                    principal_to_create_id = command.identifier.value
                    principal_to_create_password = command.password.value

                    self.__create_principal(executing_principal_id, principal_to_create_id, principal_to_create_password)
                    status_codes.append({'status': 'CREATE_PRINCIPAL'})

                elif type(command) is ChangePassword:
                    principal_to_change_id = command.identifier.value
                    principal_new_password = command.password.value

                    self.__change_password(executing_principal_id, principal_to_change_id, principal_new_password)
                    status_codes.append({'status': 'CHANGE_PASSWORD'})

                elif type(command) is Set:
                    set_variable_id = command.identifier.value
                    expression = command.expr

                    # rhs_value = self.__evaluate_expression(executing_principal_id, expression)
                    self.__set_value(executing_principal_id, set_variable_id, expression)
                    status_codes.append({'status': 'SET'})

                elif type(command) is AppendTo:

                    to_append_variable_id = command.identifier.value
                    expression_to_append = command.expr

                    # value_to_append = self.__evaluate_expression(executing_principal_id, expression)
                    self.__append_to_list(executing_principal_id, to_append_variable_id, expression_to_append)
                    status_codes.append({'status': 'APPEND'})



                elif type(command) is Local:
                    new_local_id = command.identifier.value
                    expression = command.expr

                    # rhs_value = self.__evaluate_expression(executing_principal_id, expression)
                    self.__set_local(executing_principal_id, new_local_id, expression)
                    status_codes.append({'status': 'LOCAL'})
                

                elif type(command) is Foreach:


                    container_variable_id = command.containerVarIdentifier.value
                    iter_item_id = command.itemVarIdentifier.value
                    expression = command.expr
                    
                    # record_variable = self.__evaluate_expression(expression)
                    if type(expression) is RecordIdentifier:
                        record_variable_id = expression.recordName
                        field_id = expression.recordKey

                        if record_variable_id == iter_item_id:
                            # expression.recordName = container_variable_id
                            self.__for_each_replace_field_val(executing_principal_id, container_variable_id, iter_item_id, expression)
                        else:
                            self.__for_each_replace_constant(executing_principal_id, container_variable_id, iter_item_id, expression)
                    else:
                        self.__for_each_replace_constant(executing_principal_id, container_variable_id, iter_item_id, expression)
                    status_codes.append({'status': 'FOREACH'})


                elif type(command) is SetDelegation:


                    delegator_principal_id = command.authorizerIdentifier.value
                    delegatee_principal_id = command.delegateeIdentifier.value
                    target_variable_id = command.target.value
                    if command.right == 'all':
                        delegator_principal = self.principal_map[delegator_principal_id]
                        for key, variable in delegator_principal.can_delegate_variables.items():
                            self.__set_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.READ)
                            self.__set_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.WRITE)
                            self.__set_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.APPEND)
                            self.__set_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.DELEGATE)
                    else:
                        delegation_type = {
                            'write': DelegationType.WRITE,
                            'read': DelegationType.READ,
                            'append': DelegationType.APPEND,
                            'delegate': DelegationType.DELEGATE
                        }[command.right]
                        self.__set_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, delegation_type)
                    
                    status_codes.append({'status': 'SET_DELEGATION'})



                elif type(command) is DeleteDelegation:

                    delegator_principal_id = command.authorizerIdentifier.value
                    delegatee_principal_id = command.delegateeIdentifier.value
                    target_variable_id = command.target.value
                    if command.right == 'all':
                        delegator_principal = self.principal_map[delegator_principal_id]
                        for key, variable in delegator_principal.can_delegate_variables.items():
                            self.__delete_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.READ)
                            self.__delete_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.WRITE)
                            self.__delete_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.APPEND)
                            self.__delete_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, DelegationType.DELEGATE)
                    else:
                        delegation_type = {
                            'write': DelegationType.WRITE,
                            'read': DelegationType.READ,
                            'append': DelegationType.APPEND,
                            'delegate': DelegationType.DELEGATE
                        }[command.right]
                        self.__delete_delegation(executing_principal_id, delegator_principal_id, delegatee_principal_id, target_variable_id, delegation_type)
                    status_codes.append({'status': 'DELETE_DELEGATION'})

                elif type(command) is DefaultDelegator:

                    default_delegator_id = command.defaultDelegatorIdentifier.value
                    
                    self.__set_default_delegator(executing_principal_id, default_delegator_id)
                    status_codes.append({'status': 'DEFAULT_DELEGATOR'})

                elif type(command) is ReturnValue:
                    expression = command.returnValue
                    return_value = self.__evaluate_expression(executing_principal_id, expression)
                    status_codes.append({'status': 'RETURNING', 'output': return_value})

                elif type(command) is Exit:
                    if executing_principal is not self.principal_map['admin']:
                        raise SecurityViolationException('Only admin can exit')
                    else:
                        status_codes.append({'status': 'EXITING'})
                elif type(command) is Login:
                    pass
                else:
                    pass # throw exception
            except FailureException as e:
                print(e)
                self.data_map.destroy_temp()
                self.principal_map.destroy_temp()
                return [{'status': 'FAILED'}]
            except SecurityViolationException as e:
                print(e)
                self.data_map.destroy_temp()
                self.principal_map.destroy_temp()
                return [{'status': 'DENIED'}]
    
        self.data_map.upgrade_and_destroy_temp()
        self.principal_map.upgrade_and_destroy_temp()

        return status_codes
        
