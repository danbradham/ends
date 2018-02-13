====
ends
====
Experimental DAG. This is a first pass at a prototype using Python 3 type
annotations and function signatures to make DAG node definition magical.

Simply register a function...

.. code-block:: python

    >>> import ends
    >>> @ends.register
    ... def add(a: float, b: float) -> float:
    ...     return a + b

Then create a node wrapping your registered function and add it to a graph...

.. code-block:: python

    >>> graph = ends.new_graph('simple')
    >>> add1 = graph.create('add')
    >>> add1.a.set(10.0)
    >>> add1.b.set(20.5)
    >>> graph.evaluate()
    >>> assert add1.result.get() == 30.5
    >>> assert add1.as_string() == 'add(a=10.0, b=20.5)'

The node we created wraps our original add function and provides attributes
giving us access to our annotated parameters and return value. We use result
instead of return as an attribute name so we don't collide with python's
return keyword.

From here we can register more functions, and extend our graph.

.. code-block:: python

    >>> @ends.register
    ... def minus(a: float, b: float) -> float:
    ...     return a - b
    >>> minus1 = graph.create('minus')
    >>> add1.result.connect(minus1.a)
    >>> minus1.b.set(15.5)
    >>> graph.evaluate()
    >>> assert minus1.result.get() == 15.0
    >>> assert minus1.as_string() == 'minus(a=30.5, b=15.5)'


One last thing I'm toying with is exposing parameters and results on the graph
object itself. Once you expose some parameters on a graph, you can call it,
passing in your parameters as keyword arguments. When called the exposed
attributes will be set, and the graph will be evaluated, any exposed results
will be returned. If multiple results are returned a dict will be returned.

.. code-block:: python

    >>> graph.expose(add1.a)
    >>> graph.expose(minu1.result)
    >>> assert graph(a=100.0) == 90.0


What's Next?
============

- Allow nested Graphs
- Create a lower level node abstraction to allow users to define nodes as classes and not just functions.

    + Richer initialization like custom memory allocation
    + Multiple result attributes

- Support selective branching via node success/failure?

    + This may or may not be ideal
    + It may be preferable to just create a condition node that accepts a bool and passes through one value on True and another on False

- Implement custom types to use for annotations

    + Richer type checking and validation

- GUI

    + Command pattern to support undo/redo with a history stack
    + Signals to support manipulating the graph via gui and python


Python 2.7 Compatability
========================
Although we're using Python 3's special type annotation syntax we still
have some options for Python 2.7 compatability.

- Create a custom encoding extending the base utf-8 encoding that converts py3 type hints to py2 style comment type hints.

    + "def func (a: float) -> float:" becomes "# type: (float) -> float"
    + Also add a line setting the \_\_annotations\_\_ function attribute after the function definitio

- Don't attempt to support py3 type hints at all

    + Parse py2 comment type hints and set "\_\_annotations\_\_" at registration
