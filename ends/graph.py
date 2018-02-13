# -*- coding: utf-8 -*-
__all__ = ['Graph']

from collections import defaultdict
from .func import Func, Result, Parameter, empty
from .evaluators import SerialEvaluator


class Graph:

    active = None
    _evaluator_ = SerialEvaluator
    _evaluator_params_ = {}

    def __init__(self, name):
        self.name = name
        self.connections = set()
        self.dependencies = defaultdict(set)
        self.dependents = defaultdict(set)
        self.dirty = set()
        self.nodes = {}
        self._evaluator = None
        self.set_evaluator(self._evaluator_, **self._evaluator_params_)
        self.parameters = {}
        self.results = {}

    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            self.parameters[name].set(value)
        self.evaluate()
        if len(self.results) == 1:
            return list(self.results.values())[0].get()
        else:
            return {k: v.get() for k, v in self.results.items()}

    def __getattr__(self, attr):
        if attr in self.parameters:
            return self.parameters[attr]
        elif attr in self.results:
            return self.results[attr]
        else:
            raise AttributeError('Attribute not found: attr')

    def expose(self, param_or_result, name=None):
        name = name or param_or_result.name
        if name in self.parameters.keys() + self.results.keys():
            raise AttributeError(f'Attribute already exists: {name}')

        if isinstance(param_or_result, Parameter):
            self.parameters[name] = param_or_result
        elif isinstance(param_or_result, Result):
            self.results[name] = param_or_result
        else:
            raise TypeError('param_or_result must be a Parameter or Result')

    def unexpose(self, param_or_result=None, name=None):
        assert param_or_result or name, 'Must pass Parameter, Result, or Name'

        if name:
            if self.parameters.pop(name, None):
                return
            if self.results.pop(name, None):
                return
        else:
            if isinstance(param_or_result, Parameter):
                p = param_or_result
                for name, param in list(self.parameters.items()):
                    if p is param:
                        self.parameters.pop(name)
                        return
            if isinstance(param_or_result, Result):
                r = param_or_result
                for name, result in list(self.results.items()):
                    if r is result:
                        self.results.pop(name)
                        return

            raise ValueError('param_or_result must be a Parameter or Result')

    @property
    def evaluator(self):
        return self._evaluator

    def set_evaluator(self, evaluator, *args, **kwargs):
        if self._evaluator:
            self._evaluator.uninitialize()

        self._evaluator = evaluator(self, *args, **kwargs)
        self._evaluator.initialize()

    def get_node(self, name):
        return Graph.active.nodes[name]

    def has_dirty_dependent(self, node):
        for dependency in self.dependencies[node]:
            if dependency in self.dirty:
                return True
        return False

    def create(self, func_name, name=None):
        from .api import get_func_type

        func_type = get_func_type(func_name)
        if name and not name in self.nodes:
            new_name = name
        elif name in self.nodes:
            new_name = next_name(name)
        else:
            new_name = next_name(func_name)
        new_func = func_type(new_name, graph=self)

        self.nodes[new_name] = new_func
        return new_func

    def delete(self, node):
        assert isinstance(node, Func), f'{node} must be a Func'

        node = self.nodes.pop(node.name, None)
        if node:
            for param in node.parameters:
                self.unexpose(param)
                param.disconnect()
            self.unexpose(node.result)
            node.result.disconnect()

    def connect(self, source, dest, force=False):
        assert isinstance(source, Result), f'{source} must be a Result'
        assert isinstance(dest, Parameter), f'{dest} must be a Parameter'
        if not force:
            assert not dest.incoming, f'{dest} has an incoming connection'
        assert compatible(source, dest), f'Incompatible types: {source} {dest}'
        self.detect_cycle(dest.parent, source.parent)

        self.connections.add((source, dest))
        self.dependencies[dest.parent].add(source.parent)
        self.dependents[source.parent].add(dest.parent)

        source.outgoing.add(dest)
        dest.incoming = source

        self.unclean(dest.parent)

    def disconnect(self, source, dest):
        assert isinstance(source, Result), f'{source} must be a Result'
        assert isinstance(dest, Parameter), f'{dest} must be a Parameter'

        self.connections.discard(source, dest)
        self.dependencies[dest.parent].discard(source.parent)
        self.dependents[source.parent].discard(dest.parent)

        source.outgoing.discard(dest)
        dest.incoming = None

        self.unclean(dest.parent)

    def clean(self, node):
        '''Mark the node as clean'''

        assert isinstance(node, Func), f'{node} must be a Func'

        self.dirty.discard(node)

    def unclean(self, node):
        '''Mark the node as dirty'''

        assert isinstance(node, Func), f'{node} must be a Func'

        self.dirty.add(node)

    def detect_cycle(self, dest, source):
        '''Walk tree from node, if we encounter node again, we found a cycle'''

        if dest is source:
            raise RuntimeError(f'Cycle detected')

        for dependent in self.dependents[dest]:
            self.detect_cycle(dependent, source)

    def propagate(self, node=None, visited=None):
        '''Propagate dirty flags'''

        if not node and not visited:
            visited = []
            for node in list(self.dirty):
                self.propagate(node, visited)
            return

        if node in visited:
            return

        visited.append(node)
        for dependent in self.dependents[node]:
            self.unclean(dependent)
            self.propagate(dependent, visited)

    @classmethod
    def open(self, path):
        # TODO: Open graph
        raise NotImplementedError

    def save(self):
        # TODO: Save graph
        raise NotImplementedError

    def evaluate(self):
        '''Propagate dirty flags through the graph, then evaluate all
        dirty nodes using the graph's Evaluator.
        '''

        self.propagate()
        self.evaluator.evaluate()


def next_name(func_name):
    '''Get next available name for the given func'''

    i = 1
    while True:
        name = f'{func_name}{i}'
        if name not in Graph.active.nodes:
            return name
        i += 1


def tupilize(value):

    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def compatible(source, dest):
    '''Check compatability of annotations'''

    if source == empty or dest == empty:
        return True

    s = tupilize(source.annotation)
    d = tupilize(dest.annotation)

    for t in s:
        if t in d:
            return True
    return False
