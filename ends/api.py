# -*- coding: utf-8 -*-
__all__ = [
    'NODE_TYPES',
    'GRAPHS',
    'register',
    'unregister',
    'get_func_type',
    'set_graph',
    'get_graph',
    'new_graph',
    'save_graph',
    'open_graph',
    'evaluate',
    'create',
    'delete',
    'connect',
    'disconnect'
]

from .graph import Graph
from .func import FuncType


NODE_TYPES = {}
GRAPHS = {}


def register(func):
    '''Register function'''

    if func.__name__ in NODE_TYPES:
        raise NameError(f'Function already registered: {func.__name__}')
    NODE_TYPES[func.__name__] = FuncType(func)
    # TODO: Python 2 does not set __annotations__
    #       Set it here or use custom utf-8 encoding to do so


def unregister(func):
    '''Unregister function'''

    NODE_TYPES.pop(func.__name__, None)


def get_func_type(name):
    '''Get Func from registry by name'''

    if not name in NODE_TYPES:
        raise NameError(f'Unregistered node type: {name}')
    return NODE_TYPES[name]


def set_graph(graph):
    '''Set the active graph'''

    Graph.active = graph


def get_graph(name=None):
    '''Get the active graph'''

    return GRAPHS.get(name, Graph.active)


def new_graph(name):
    '''Create new graph and make it the active graph'''

    Graph.active = Graph(name)
    return Graph.active


def save_graph(path):
    '''Save the active graph'''

    Graph.active.save(path)


def open_graph(path):
    '''Open a graph and make it the active graph'''

    Graph.active = Graph.open(path)
    return Graph.active


# This part of the api allows interacting with the active Graph implicitly
# Do I like this?


def evaluate():
    '''Evaluate the active graph'''

    Graph.active.evaluate()


def create(func_name, name=None):
    '''Create a node of the given func type'''

    return Graph.active.create(func_name, name)


def delete(node):
    '''Delete node'''

    Graph.active.delete(node)


def connect(source, *destinations):
    '''Connect node result to a node parameter'''

    for destination in destinations:
        Graph.active.connect(source, destination)


def disconnect(source, destination):
    '''Disconnect node parameter from node result'''

    Graph.active.disconnect(source, destination)
