# -*- coding: utf-8 -*-
from timeit import default_timer
import textwrap
import time
import sys
import ends


@ends.register
def add(a: float, b: float) -> float:
    return a + b

@ends.register
def minus(a: float, b: float) -> float:
    return a - b

@ends.register
def multiply(a: float, b: float) -> float:
    return a * b

@ends.register
def divide(a: float, b: float) -> float:
    return a / b

@ends.register
def slow_add(a: float, b: float) -> float:
    time.sleep(0.1)
    return a + b


def simple_graph():
    print('\n[]-[]-[]\n')
    print('Creating and validating simple_graph...', end='')
    # Create a new graph
    graph = ends.new_graph('simple_graph')

    # Create some nodes
    add1 = graph.create('add')
    minus1 = graph.create('minus')
    mult1 = graph.create('multiply')
    div1 = graph.create('divide')

    # Set some parameters
    add1.a.set(10.0)
    add1.b.set(20.0)
    minus1.a.set(100.0)
    div1.b.set(2.0)

    # Make some connections
    graph.connect(add1.result, minus1.b)
    graph.connect(add1.result, mult1.a)
    graph.connect(minus1.result, mult1.b)
    graph.connect(mult1.result, div1.a)

    # Detect a cycle
    try:
        graph.connect(div1.result, add1.a)
    except RuntimeError:
        assert True  # Found a cycle
    else:
        assert False # Did not find a cycle

    # Evaluate our graph once
    graph.evaluate()

    # Validate our results
    def validate():
        assert not graph.dirty
        assert add1.result.get() == 30.0
        assert minus1.result.get() == 70.0
        assert mult1.result.get() == 2100.0
        assert div1.result.get() == 1050.0

    validate()
    print('OK!')
    return graph, add1, validate


def complex_graph():
    print(
        '\n   []\n'
        '  /  \\\n'
        '[]    []\n'
    )
    print('Creating and validating complex_graph...', end='')
    graph = ends.new_graph('complex_graph')

    def branch(node, n, leaf_nodes=None):
        if n == 0:
            leaf_nodes.append(node)
            return
        anode = graph.create('slow_add')
        bnode = graph.create('slow_add')
        graph.connect(node.result, anode.a)
        graph.connect(node.result, bnode.a)
        anode.b.set(10.0)
        bnode.b.set(10.0)
        branch(anode, n-1, leaf_nodes)

    root = graph.create('slow_add')
    root.a.set(10.0)
    root.b.set(10.0)
    leaf_nodes = []
    branch(root, n=10, leaf_nodes=leaf_nodes)

    def validate():
        for node in leaf_nodes:
            assert node.result.get() == 120.0

    graph.evaluate()
    validate()
    print('OK!')
    return graph, root, validate


def benchmark_graph(graph, root, n, validator=None):

    # Serial
    print(f'SerialEvaluator {n} times', end='')
    total = 0
    for i in range(n):
        # Evaluate the graph
        sys.stdout.write('.')
        sys.stdout.flush()
        graph.unclean(root)
        st = default_timer()
        graph.evaluate()
        total += default_timer() - st
        if validator:
            validator()
    print('DONE!')
    print(f'{total:0.10f} seconds', end='\n\n')

    # Switch to multiprocessing + cloudpickle
    print(f'ParallelEvaluator {n} times', end='')
    graph.set_evaluator(ends.ParallelEvaluator)
    total = 0
    for i in range(n):
        # Evaluate the graph
        sys.stdout.write('.')
        sys.stdout.flush()
        graph.unclean(root)
        st = default_timer()
        graph.evaluate()
        total += default_timer() - st
        if validator:
            validator()
    print('DONE!')
    print(f'{total:0.10f} seconds')
    print('')


if __name__ == '__main__':

    graph, root, validator = simple_graph()
    benchmark_graph(graph, root, 10, validator)

    graph, root, validator = complex_graph()
    benchmark_graph(graph, root, 10, validator)

    # Notes
    print(textwrap.dedent(
        '''
        Summary:
            Multiprocessing intoduces too much overhead for simple_graph.
            simple_graph is a "straight" graph, where each task is connected
            to the result of the previous, therefore the evaluation must be
            sequential.

            We see the tables turn when evaluating the complex_graph. The
            complex_graph is a giant tree that has a lot of long running tasks
            that don't depend on each other. In this scenario the price of
            sending tasks between processes is less than the value gained by
            parallelism.

        Notes:
            Everything is easier when evaluated serially, shared memory is
            a given for one thing and it requires no synchronization.

            With multiprocessing, ctypes can be used to share memory between
            processes. Generic serialization of tasks is handled by
            cloudpickle. Overhead can be reduced by selectively marking tasks
            to be submitted to the process pool. Small fast tasks can be
            executed in the main thread.
        '''
    ))
