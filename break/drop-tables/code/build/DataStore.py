import itertools
import networkx as nx
from enum import Enum
from copy import deepcopy

class DelegationType(Enum):
    READ = 0,
    WRITE = 1,
    APPEND = 2,
    DELEGATE = 3


ADMIN_ID = "admin"
ANYONE_ID = "anyone"
class DataVariable:
    
    def __init__(self, creator_id, value):
        if type(creator_id) is not str:
            raise TypeError(type(creator_id))
        self.creator_id = creator_id

        # print(value)
        self.value = value
        self.read_delegation_graph = nx.DiGraph()
        self.write_delegation_graph = nx.DiGraph()
        self.append_delegation_graph = nx.DiGraph()
        self.delegate_delegation_graph = nx.DiGraph()

        self.read_delegation_graph.add_edge(ADMIN_ID, creator_id)
        self.write_delegation_graph.add_edge(ADMIN_ID, creator_id)
        self.append_delegation_graph.add_edge(ADMIN_ID, creator_id)
        self.delegate_delegation_graph.add_edge(ADMIN_ID, creator_id)
        
        self.read_delegation_graph.add_node(ANYONE_ID)
        self.write_delegation_graph.add_node(ANYONE_ID)
        self.append_delegation_graph.add_node(ANYONE_ID)
        self.delegate_delegation_graph.add_node(ANYONE_ID)

    def __del__(self):
        del self.value
        del self.read_delegation_graph
        del self.write_delegation_graph
        del self.append_delegation_graph
        del self.delegate_delegation_graph
    
    def _get_delegation_graph(self, delegation_type):
        if delegation_type == DelegationType.READ:
            return self.read_delegation_graph 
        elif delegation_type == DelegationType.WRITE:
            return self.write_delegation_graph
        elif delegation_type == DelegationType.APPEND:
            return self.append_delegation_graph
        elif delegation_type == DelegationType.DELEGATE:
            return self.delegate_delegation_graph
        else:
            pass


    def add_delegation(self, delegator_principal, delegatee_principal, delegation_type):
        if type(delegator_principal) is not str:
            raise TypeError(type(principal))
        if type(delegatee_principal) is not str:
            raise TypeError(type(principal))
        
        delegation_graph = self._get_delegation_graph(delegation_type)

        if delegator_principal not in delegation_graph:
            pass
        if delegatee_principal not in delegation_graph:
            pass
        
        delegation_graph.add_edge(delegator_principal, delegatee_principal)

    def remove_delegation(self, delegator_principal, delegatee_principal, delegation_type):
        if type(delegator_principal) is not str:
            raise TypeError(type(principal))
        if type(delegatee_principal) is not str:
            raise TypeError(type(principal))

        if delegatee_principal == ADMIN_ID:
            return

        delegation_graph = self._get_delegation_graph(delegation_type)

        if delegator_principal not in delegation_graph:
            pass
        if delegatee_principal not in delegation_graph:
            pass

        try:
            delegation_graph.remove_edge(delegator_principal, delegatee_principal)
        except nx.exception.NetworkXError:
            pass
    # def __str__(self):
    #     return str(self.value)

    def is_delegated_to(self, principal, delegation_type):
        if type(principal) is not str:
            raise TypeError(type(principal))

        try:
            if delegation_type == DelegationType.READ:
                return (nx.has_path(self.read_delegation_graph, ADMIN_ID, principal) or
                        nx.has_path(self.read_delegation_graph, ADMIN_ID, ANYONE_ID))
            elif delegation_type == DelegationType.WRITE:
                return (nx.has_path(self.write_delegation_graph, ADMIN_ID, principal) or
                        nx.has_path(self.write_delegation_graph, ADMIN_ID, ANYONE_ID))
            elif delegation_type == DelegationType.APPEND:
                return (nx.has_path(self.append_delegation_graph, ADMIN_ID, principal) or
                        nx.has_path(self.append_delegation_graph, ADMIN_ID, ANYONE_ID))
            elif delegation_type == DelegationType.DELEGATE:
                # print(f'principal {principal} has delegation privilage?')
                return (nx.has_path(self.delegate_delegation_graph, ADMIN_ID, principal) or
                        nx.has_path(self.delegate_delegation_graph, ADMIN_ID, ANYONE_ID))
            else:
                pass
        except nx.exception.NodeNotFound:
            return False


class DataStore:

    def __init__(self, global_data=dict()):
        self.local_data = dict()
        self.global_data = global_data
        self.temp_data = dict()
    
    def __del__(self):
        # self.local_data = None
        # self.global_data = None
        # self.temp_data = None
        # idk why I need to do this
        self.local_data.clear()
        self.global_data.clear()
        self.temp_data.clear()
    
    def __getitem__(self, key):
        # prioritize temp_data
        if key in self.temp_data:
            return self.temp_data[key]
        elif key in self.global_data:
            self.temp_data[key] = deepcopy(self.global_data[key])
            return self.temp_data[key]
        elif key in self.local_data:
            return self.local_data[key]
        else:
            self.__missing__(key)

    def __contains__(self, item):
        # item is really key
        return (item in self.temp_data) or (item in self.global_data) or (item in self.local_data)

    def __missing__(self, key):
        raise KeyError(key)

    def set_value(self, key, value, isLocal = False):

        if isLocal:
            if key in self.global_data or key in self.temp_data:
                pass # throw exception
            
            self.local_data[key] = value

        else:
            if key in self.local_data:
                pass # throw exception
            self.temp_data[key] = value
        
    def upgrade_and_destroy_temp(self):

        for key, value in self.temp_data.items():
            self.global_data[key] = value
        self.destroy_temp()
    
    def destroy_temp(self):
        self.temp_data.clear()
        self.local_data.clear()


    def is_local(self, key):
        if key in self.local_data:
            return True
        elif key in self.temp_data or key in self.global_data:
            return False
        else:
            raise KeyError(key) # throw exception

    def items(self):
        return itertools.chain(self.temp_data.items(), self.global_data.items(), self.temp_data.items())


class Principal:

    def __init__(self, password):
        self.password = password
        self.can_delegate_variables = {}

    def __del__(self):
        del self.password
        del self.can_delegate_variables
        


if __name__ == '__main__':
    # socket connection etc
    pass