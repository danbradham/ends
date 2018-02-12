# -*- coding: utf-8 -*-
__all__ = ['SerialEvaluator']

class SerialEvaluator:
    '''Provides Serial Evaluation of a Graph.'''

    def __init__(self, graph):
        self.graph = graph

    def initialize(self):
        pass

    def uninitialize(self):
        pass

    def ready(self):
        for node in list(self.graph.dirty):
            if not self.graph.has_dirty_dependent(node):
                yield node

    def evaluate(self):
        while self.graph.dirty:
            for node in self.ready():
                node.apply()
