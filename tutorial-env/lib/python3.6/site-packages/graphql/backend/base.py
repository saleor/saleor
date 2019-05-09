from ..pyutils.cached_property import cached_property
from ..language import ast

from abc import ABCMeta, abstractmethod
import six


# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Dict, Optional, Union, Callable
    from ..language.ast import Document
    from ..type.schema import GraphQLSchema


class GraphQLBackend(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def document_from_string(self, schema, request_string):
        raise NotImplementedError(
            "document_from_string method not implemented in {}.".format(self.__class__)
        )


class GraphQLDocument(object):
    def __init__(self, schema, document_string, document_ast, execute):
        # type: (GraphQLSchema, str, Document, Callable) -> None
        self.schema = schema
        self.document_string = document_string
        self.document_ast = document_ast
        self.execute = execute

    @cached_property
    def operations_map(self):
        # type: () -> Dict[Union[str, None], str]
        """
        returns a Mapping of operation names and it's associated types.
        E.g. {'myQuery': 'query', 'myMutation': 'mutation'}
        """
        document_ast = self.document_ast
        operations = {}  # type: Dict[Union[str, None], str]
        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                if definition.name:
                    operations[definition.name.value] = definition.operation
                else:
                    operations[None] = definition.operation

        return operations

    def get_operation_type(self, operation_name):
        # type: (Optional[str]) -> Optional[str]
        """
        Returns the operation type ('query', 'mutation', 'subscription' or None)
        for the given operation_name.
        If no operation_name is provided (and only one operation exists) it will return the
        operation type for that operation
        """
        operations_map = self.operations_map
        if not operation_name and len(operations_map) == 1:
            return next(iter(operations_map.values()))
        return operations_map.get(operation_name)
