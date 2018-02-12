# -*- coding: utf-8 -*-
__all__ = ['Parameter', 'Result', 'Func', 'FuncType', 'empty']

try:
    from inspect import signature, Parameter
    empty = Parameter.empty
except NameError:  # py2 compat
    from funcsigs import signature, Parameter
    empty = Parameter.empty


class Parameter:
    '''Descriptor of a Func parameter described by type a annotation'''

    def __init__(self, name, annotation, default, parent, graph=None):
        self.name = name
        self.annotation = annotation
        self.default = default
        self.parent = parent
        self.graph = graph
        self.incoming = None
        self._value = default

    def __str__(self):
        return f'{self.parent.name}.{self.name}'

    def check(self, value):
        if self.annotation is empty:
            return
        if not isinstance(value, self.annotation):
            raise TypeError(
                f'Parameter "{self.name}" must be {self.annotation} '
              + f'not {type(value)}'
            )

    def get(self):
        if self.incoming:
            return self.incoming.get()
        return self._value

    def set(self, value):
        if self.incoming:
            raise AttributeError(f'{self} has an incoming connection')
        self.check(value)
        self._value = value
        self.graph.unclean(self.parent)

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        self.graph.disconnect(self.incoming, self)


class Result:
    '''Descriptor of a Func return value described by a type annotation'''

    def __init__(self, annotation, parent, graph=None):
        self.name = 'result'
        self.annotation = annotation
        self.parent = parent
        self.graph = graph
        self.outgoing = set()
        self._value = None

    def __str__(self):
        return f'{self.parent.name}.{self.name}'

    def check(self, value):
        if self.annotation is empty:
            return
        if not isinstance(value, self.annotation):
            raise TypeError(
                f'Return value must be {self.annotation}.'
              + f'Got {type(value)}'
            )

    def get(self):
        return self._value

    def set(self, value):
        self.check(value)
        self._value = value
        self.graph.clean(self.parent)

    def connect(self, param, force=False):
        self.graph.connect(self, param, force)

    def disconnect(self):
        for param in self.outgoing:
            self.graph.disconnect(self, param)


class Func:
    '''Provides a validated interface to a function with type annotations'''

    __func__ = None
    __signature__ = None

    def __init__(self, name, graph=None):
        self.name = name
        self.graph = init_graph(graph)
        self.parameters = []
        self.__init_params__()

    def __init_params__(self):

        for name, param in self.__signature__.parameters.items():
            p = Parameter(
                name,
                param.annotation,
                param.default,
                self,
                self.graph
            )
            setattr(self, name, p)
            self.parameters.append(p)

        self.result = Result(
            self.__signature__.return_annotation,
            self,
            self.graph
        )

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)

    def __str__(self):
        return self.as_string()

    @property
    def dirty(self):
        return self in self.graph.dirty

    @dirty.setter
    def dirty(self, value):
        if value:
            self.graph.unclean(self)
        else:
            self.graph.clean(self)

    def as_string(self):
        args, kwargs = self.args_kwargs()
        params = []
        for arg in args:
            params.append(f'{arg}')
        for k, v in kwargs.items():
            params.append(f'{k}={v}')
        params = ', '.join(params)
        return f'{self.__func__.__name__}({params})'

    def args_kwargs(self):
        args = []
        kwargs = {}
        for name, param in self.__signature__.parameters.items():
            value = getattr(self, name).get()
            if param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD):
                kwargs[name] = value
            elif param.kind == param.VAR_KEYWORD:
                kwargs.update(value)
            elif param.kind == param.POSITIONAL_ONLY:
                args.append(value)
            elif param.kind == param.VAR_POSITIONAL:
                args.extend(value)
        return tuple(args), kwargs

    def apply(self):
        args, kwargs = self.args_kwargs()
        result = self.__func__(*args, **kwargs)
        self.result.set(result)


def init_graph(graph=None):
    if graph:
        return graph
    if not Graph.active:
        raise RuntimeError('No active Graph...')
    return Graph.active


def FuncType(func):
    '''Func factory. Create a new Func type for the given function'''

    return type(
        func.__name__,
        (Func,),
        dict(
            __func__=staticmethod(func),
            __signature__=signature(func)
        )
    )
