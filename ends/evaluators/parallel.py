# -*- coding: utf-8 -*-
'''
Parallel Evaluator
==================

Leverages the multiprocessing library to provide parallel evaluation of the
graph.
'''
__all__ = ['FuncTask', 'ProcessPool', 'ParallelEvaluator']

import time
import multiprocessing
import cloudpickle
import pickle


class FuncTask(object):

    def __init__(self, func):
        self.func = func
        self.result = None
        self.exc = None

    def __call__(self, *args, **kwargs):
        func = pickle.loads(self.func)
        try:
            self.result = func(*args, **kwargs)
        except Exception as e:
            self.exc = e
        return self


class ProcessPool:
    '''ProcessPool using stdlib multiprocessing.

    Generic objects supported using cloudpickle.
    '''

    def __init__(self, processes=None):
        self.processes = processes or multiprocessing.cpu_count()
        self.pending = {}
        self.pool = None

    def start(self):
        self.pool = multiprocessing.Pool(processes=self.processes)

    def stop(self):
        self.pool.terminate()
        self.pool = None

    def submit(self, node):
        args, kwargs = node.args_kwargs()
        result = self.pool.apply_async(
            FuncTask(cloudpickle.dumps(node.__func__)),
            args=args,
            kwds=kwargs,
            callback=self.apply_result(node)
        )
        self.pending[node] = result

    def apply_result(self, node):
        def apply_result_to_node(task):
            if task.exc:
                raise task.exc
            self.pending.pop(node)
            node.result.set(task.result)
        return apply_result_to_node


class ParallelEvaluator:

    _pool_ = ProcessPool

    def __init__(self, graph, processes=4):
        self.graph = graph
        self.processes = processes
        self.pool = None

    def initialize(self):
        self.pool = self._pool_(processes=self.processes)
        self.pool.start()

    def uninitialize(self):
        self.pool.stop()

    def ready(self):
        for node in list(self.graph.dirty):

            if self.graph.has_dirty_dependent(node):
                continue

            if node in self.pool.pending:
                continue

            yield node

    def evaluate(self):
        while self.graph.dirty:
            for node in self.ready():
                self.pool.submit(node)
            time.sleep(0.001)  # Allow enough time to run async callbacks
