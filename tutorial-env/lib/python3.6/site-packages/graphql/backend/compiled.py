from six import string_types
from .base import GraphQLDocument

# Necessary for static type checking
if False:  # flake8: noqa
    from ..type.schema import GraphQLSchema
    from typing import Any, Optional, Dict, Callable, Union


class GraphQLCompiledDocument(GraphQLDocument):
    @classmethod
    def from_code(
        cls,
        schema,  # type: GraphQLSchema
        code,  # type: Union[str, Any]
        uptodate=None,  # type: Optional[bool]
        extra_namespace=None,  # type: Optional[Dict[str, Any]]
    ):
        # type: (...) -> GraphQLCompiledDocument
        """Creates a GraphQLDocument object from compiled code and the globals.  This
        is used by the loaders and schema to create a document object.
        """
        if isinstance(code, string_types):
            filename = "<document>"
            code = compile(code, filename, "exec")
        namespace = {"__file__": code.co_filename}
        exec(code, namespace)
        if extra_namespace:
            namespace.update(extra_namespace)
        rv = cls._from_namespace(schema, namespace)
        # rv._uptodate = uptodate
        return rv

    @classmethod
    def from_module_dict(cls, schema, module_dict):
        # type: (GraphQLSchema, Dict[str, Any]) -> GraphQLCompiledDocument
        """Creates a template object from a module.  This is used by the
        module loader to create a document object.
        """
        return cls._from_namespace(schema, module_dict)

    @classmethod
    def _from_namespace(cls, schema, namespace):
        # type: (GraphQLSchema, Dict[str, Any]) -> GraphQLCompiledDocument
        document_string = namespace.get("document_string", "")  # type: str
        document_ast = namespace.get("document_ast")  # type: ignore
        execute = namespace["execute"]  # type: Callable

        namespace["schema"] = schema
        return cls(  # type: ignore
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=execute,
        )
